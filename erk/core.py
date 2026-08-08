from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import IntEnum, StrEnum
import hashlib
import json
import math
from types import MappingProxyType
from typing import Any, Mapping, Sequence


class Authority(IntEnum):
    OBSERVE = 0
    SIMULATE = 1
    EXECUTE = 2


class Action(StrEnum):
    BLOCK = "BLOCK"
    BRANCH = "BRANCH"
    REJECT = "REJECT"
    QUARANTINE = "QUARANTINE"
    ENABLE_EXECUTION = "ENABLE_EXECUTION"
    ESCALATE = "ESCALATE"
    ARCHIVE = "ARCHIVE"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping): return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    if isinstance(value, set): return frozenset(_freeze(v) for v in value)
    if isinstance(value, tuple): return tuple(_freeze(v) for v in value)
    return value


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping): return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)): return [_canonical(v) for v in value]
    if isinstance(value, (set, frozenset)): return sorted((_canonical(v) for v in value), key=repr)
    return value


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    source: str
    timestamp: str
    payload: Mapping[str, Any]
    authority_grant: int | None = None
    authority_signature: str = ""
    provenance_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze(self.payload))
        digest = hashlib.sha256(self._canonical_content()).hexdigest()
        if self.provenance_hash and self.provenance_hash != digest: raise ValueError("provenance_hash does not match immutable evidence")
        object.__setattr__(self, "provenance_hash", digest)

    def _canonical_content(self) -> bytes:
        obj = {"evidence_id": self.evidence_id, "source": self.source, "timestamp": self.timestamp, "payload": _canonical(self.payload), "authority_grant": self.authority_grant, "authority_signature": self.authority_signature}
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    prior: Authority
    target: Authority
    evidence_hash: str
    state_hash: str
    policy_hash: str
    branch_id: str
    nonce: str
    grant_id: str
    kernel_signature: str

    def message(self) -> bytes:
        obj = {"prior": int(self.prior), "target": int(self.target), "evidence_hash": self.evidence_hash, "state_hash": self.state_hash, "policy_hash": self.policy_hash, "branch_id": self.branch_id, "nonce": self.nonce, "grant_id": self.grant_id}
        return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def verify_authority_grant(grant: AuthorityGrant, state: "EpistemicState", evidence: Sequence[EvidenceRecord], kernel_secret: bytes, consumed_nonces: frozenset[str] = frozenset()) -> bool:
    if grant.nonce in consumed_nonces: return False
    if grant.prior != state.authority or grant.target != Authority(int(grant.prior) + 1): return False
    if grant.branch_id != state.branch_id: return False
    evidence_hash = hashlib.sha256(b"".join(e._canonical_content() for e in evidence)).hexdigest()
    if evidence_hash != grant.evidence_hash or grant.state_hash != state_hash(state) or grant.policy_hash != state.policy_version: return False
    expected = hashlib.sha256(kernel_secret + grant.message()).hexdigest()
    return grant.kernel_signature == expected


@dataclass(frozen=True, slots=True)
class GraphNode:
    node_id: str
    kind: str
    supported: bool = True


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    kind: str = "DEPENDS_ON"


@dataclass(frozen=True, slots=True)
class GraphMetrics:
    unsupported_depth: int
    critical_load: Mapping[str, int]
    cycles: tuple[tuple[str, ...], ...]


def graph_metrics(nodes: Sequence[GraphNode], edges: Sequence[GraphEdge]) -> GraphMetrics:
    ids = {n.node_id for n in nodes}; adjacency: dict[str, list[str]] = {n: [] for n in ids}
    for edge in edges:
        if edge.kind == "DEPENDS_ON" and edge.source in ids and edge.target in ids: adjacency[edge.source].append(edge.target)
    cycles: list[tuple[str, ...]] = []; color = {n: 0 for n in ids}; stack: list[str] = []
    def dfs(node: str) -> None:
        color[node] = 1; stack.append(node)
        for nxt in adjacency[node]:
            if color[nxt] == 0: dfs(nxt)
            elif color[nxt] == 1 and nxt in stack: cycles.append(tuple(stack[stack.index(nxt):] + [nxt]))
        stack.pop(); color[node] = 2
    for node in sorted(ids):
        if color[node] == 0: dfs(node)
    memo: dict[str, int] = {}
    def depth(node: str, visiting: set[str]) -> int:
        if node in memo: return memo[node]
        if node in visiting: return 0
        visiting.add(node); value = max((1 + depth(nxt, visiting) for nxt in adjacency[node]), default=0); visiting.remove(node); memo[node] = value; return value
    unsupported = {n.node_id for n in nodes if not n.supported}; critical: dict[str, int] = {}
    for node in sorted(ids):
        seen: set[str] = set(); todo = list(adjacency[node])
        while todo:
            nxt = todo.pop()
            if nxt in seen: continue
            seen.add(nxt); todo.extend(adjacency[nxt])
        critical[node] = len(seen)
    return GraphMetrics(max((depth(n, set()) for n in unsupported), default=0), MappingProxyType(critical), tuple(cycles))


def _prediction_distance(a: Any, b: Any) -> float:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)): return min(1.0, abs(float(a) - float(b)))
    return 0.0 if a == b else 1.0


def compute_strain(hypotheses: Mapping[str, float], predictions: Mapping[str, Mapping[str, Any]], observability: Mapping[str, float], relevance: Mapping[str, float] | None = None, lam: float = 1.0) -> float:
    if not hypotheses or lam < 0: return 0.0
    total = sum(max(0.0, float(p)) for p in hypotheses.values())
    if total <= 0: return 0.0
    probs = {h: max(0.0, float(p)) / total for h, p in hypotheses.items()}; relevance = relevance or {}; conflict = 0.0; names = list(probs)
    for i, h1 in enumerate(names):
        for h2 in names[i + 1:]:
            conflict += probs[h1] * probs[h2] * sum(max(0.0, float(relevance.get(v, 1.0))) * float(obs) * _prediction_distance(predictions.get(h1, {}).get(v), predictions.get(h2, {}).get(v)) for v, obs in observability.items() if obs > 0)
    return 1.0 - math.exp(-max(0.0, lam) * conflict)


@dataclass(frozen=True, slots=True)
class EpistemicState:
    observability: Mapping[str, float] = field(default_factory=dict)
    hypotheses: Mapping[str, float] = field(default_factory=dict)
    predictions: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    relevance: Mapping[str, float] = field(default_factory=dict)
    strain: float = 0.0
    unsupported_depth: int = 0
    critical_load: Mapping[str, int] = field(default_factory=dict)
    cycles: tuple[tuple[str, ...], ...] = ()
    authority: Authority = Authority.OBSERVE
    calibration_error: float = 0.0
    active_branches: int = 1
    evidence_count: int = 0
    policy_version: str = "erk-v2.2"
    branch_id: str = "root"
    terminal: str | None = None
    def __post_init__(self) -> None:
        for name in ("observability", "hypotheses", "predictions", "relevance", "critical_load"): object.__setattr__(self, name, _freeze(getattr(self, name)))
    def normalized(self) -> "EpistemicState":
        return replace(self, observability={k: min(1.0, max(0.0, float(v))) for k, v in self.observability.items()}, strain=min(1.0, max(0.0, float(self.strain))), calibration_error=min(1.0, max(0.0, float(self.calibration_error))), active_branches=max(0, int(self.active_branches)), evidence_count=max(0, int(self.evidence_count)))


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    u_crit: float = .80
    depth_bound: int = 8
    calibration_crit: float = .25
    branch_bound: int = 16
    cost_weights: Mapping[Action, float] = field(default_factory=lambda: {Action.BLOCK:.20, Action.BRANCH:.40, Action.ARCHIVE:.60, Action.QUARANTINE:.80, Action.REJECT:1.0, Action.ESCALATE:.90, Action.ENABLE_EXECUTION:0.0})
    def __post_init__(self) -> None: object.__setattr__(self, "cost_weights", _freeze(self.cost_weights))


class Supervisor:
    def __init__(self, config: PolicyConfig | None = None) -> None: self.config = config or PolicyConfig()
    def safe_actions(self, state: EpistemicState) -> tuple[Action, ...]:
        s = state.normalized()
        if s.terminal is not None: return ()
        if s.cycles: return (Action.REJECT, Action.QUARANTINE, Action.ESCALATE)
        safe = [Action.BLOCK, Action.BRANCH, Action.REJECT, Action.QUARANTINE, Action.ESCALATE, Action.ARCHIVE]
        if s.authority == Authority.EXECUTE and s.strain < self.config.u_crit and s.unsupported_depth < self.config.depth_bound and s.calibration_error < self.config.calibration_crit and s.active_branches <= self.config.branch_bound: safe.append(Action.ENABLE_EXECUTION)
        return tuple(safe)
    def supervise(self, state: EpistemicState) -> Action:
        actions = self.safe_actions(state)
        return Action.ESCALATE if not actions else min(actions, key=lambda a: (self.config.cost_weights.get(a, 1.0), a.value))


class Transition:
    @staticmethod
    def apply(state: EpistemicState, action: Action, evidence: Sequence[EvidenceRecord] = (), grant: AuthorityGrant | None = None, kernel_secret: bytes | None = None, consumed_nonces: frozenset[str] = frozenset()) -> EpistemicState:
        s = state.normalized(); evidence = tuple(evidence)
        if s.terminal is not None: raise ValueError("terminal branch cannot transition")
        if action == Action.ENABLE_EXECUTION:
            if s.authority != Authority.EXECUTE: raise ValueError("execution requires authority=EXECUTE")
            return replace(s, authority=Authority.SIMULATE)
        next_authority = s.authority
        if grant is not None:
            if kernel_secret is None or not verify_authority_grant(grant, s, evidence, kernel_secret, consumed_nonces): raise ValueError("invalid or replayed kernel authority grant")
            next_authority = grant.target
        return replace(s, authority=next_authority, evidence_count=s.evidence_count + len(evidence)).normalized()


def state_hash(state: EpistemicState) -> str:
    obj = {"observability":dict(sorted(state.observability.items())),"hypotheses":dict(sorted(state.hypotheses.items())),"predictions":{k:dict(sorted(v.items())) for k,v in sorted(state.predictions.items())},"relevance":dict(sorted(state.relevance.items())),"strain":state.strain,"unsupported_depth":state.unsupported_depth,"critical_load":dict(sorted(state.critical_load.items())),"cycles":state.cycles,"authority":int(state.authority),"calibration_error":state.calibration_error,"active_branches":state.active_branches,"evidence_count":state.evidence_count,"policy_version":state.policy_version,"branch_id":state.branch_id,"terminal":state.terminal}
    return hashlib.sha256(json.dumps(_canonical(obj), sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
