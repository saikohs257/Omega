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
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    """Immutable evidence; the digest is derived from canonical content."""

    evidence_id: str
    source: str
    timestamp: str
    payload: Mapping[str, Any]
    authority_grant: int | None = None
    provenance_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze(self.payload))
        canonical = self._canonical_content()
        digest = hashlib.sha256(canonical).hexdigest()
        if self.provenance_hash and self.provenance_hash != digest:
            raise ValueError("provenance_hash does not match immutable evidence")
        object.__setattr__(self, "provenance_hash", digest)

    def _canonical_content(self) -> bytes:
        obj = {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "authority_grant": self.authority_grant,
        }
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


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
    ids = {n.node_id for n in nodes}
    adjacency: dict[str, list[str]] = {n: [] for n in ids}
    for edge in edges:
        if edge.kind == "DEPENDS_ON" and edge.source in ids and edge.target in ids:
            adjacency[edge.source].append(edge.target)

    cycles: list[tuple[str, ...]] = []
    color: dict[str, int] = {n: 0 for n in ids}
    stack: list[str] = []

    def dfs_cycle(node: str) -> None:
        color[node] = 1
        stack.append(node)
        for nxt in adjacency[node]:
            if color[nxt] == 0:
                dfs_cycle(nxt)
            elif color[nxt] == 1 and nxt in stack:
                i = stack.index(nxt)
                cycles.append(tuple(stack[i:] + [nxt]))
        stack.pop()
        color[node] = 2

    for node in sorted(ids):
        if color[node] == 0:
            dfs_cycle(node)

    memo_depth: dict[str, int] = {}

    def depth(node: str, visiting: set[str]) -> int:
        if node in memo_depth:
            return memo_depth[node]
        if node in visiting:
            return 0
        visiting.add(node)
        value = max((1 + depth(nxt, visiting) for nxt in adjacency[node]), default=0)
        visiting.remove(node)
        memo_depth[node] = value
        return value

    unsupported = {n.node_id for n in nodes if not n.supported}
    unsupported_depth = max((depth(n, set()) for n in unsupported), default=0)

    critical_load: dict[str, int] = {}
    for node in sorted(ids):
        seen: set[str] = set()
        todo = list(adjacency[node])
        while todo:
            nxt = todo.pop()
            if nxt in seen:
                continue
            seen.add(nxt)
            todo.extend(adjacency[nxt])
        critical_load[node] = len(seen)

    return GraphMetrics(unsupported_depth, critical_load, tuple(cycles))


def _prediction_distance(a: Any, b: Any) -> float:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return min(1.0, abs(float(a) - float(b)))
    return 0.0 if a == b else 1.0


def compute_strain(
    hypotheses: Mapping[str, float],
    predictions: Mapping[str, Mapping[str, Any]],
    observability: Mapping[str, float],
    relevance: Mapping[str, float] | None = None,
    lam: float = 1.0,
) -> float:
    """Decision-relevant weighted disagreement; graph topology does not define strain."""
    if not hypotheses or lam < 0:
        return 0.0
    total_prob = sum(max(0.0, float(p)) for p in hypotheses.values())
    if total_prob <= 0:
        return 0.0
    probs = {h: max(0.0, float(p)) / total_prob for h, p in hypotheses.items()}
    relevance = relevance or {}
    conflict = 0.0
    names = list(probs)
    for i, h1 in enumerate(names):
        for h2 in names[i + 1 :]:
            pair_weight = probs[h1] * probs[h2]
            disagreement = 0.0
            for variable, obs in observability.items():
                if obs <= 0:
                    continue
                w = max(0.0, float(relevance.get(variable, 1.0)))
                disagreement += w * float(obs) * _prediction_distance(
                    predictions.get(h1, {}).get(variable),
                    predictions.get(h2, {}).get(variable),
                )
            conflict += pair_weight * disagreement
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

    def normalized(self) -> EpistemicState:
        obs = {k: min(1.0, max(0.0, float(v))) for k, v in self.observability.items()}
        return replace(self, observability=obs, strain=min(1.0, max(0.0, float(self.strain))), calibration_error=min(1.0, max(0.0, float(self.calibration_error))), active_branches=max(0, int(self.active_branches)), evidence_count=max(0, int(self.evidence_count)))


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    u_crit: float = 0.80
    depth_bound: int = 8
    calibration_crit: float = 0.25
    branch_bound: int = 16
    cost_weights: Mapping[Action, float] = field(default_factory=lambda: {Action.BLOCK: 0.20, Action.BRANCH: 0.40, Action.ARCHIVE: 0.60, Action.QUARANTINE: 0.80, Action.REJECT: 1.00, Action.ESCALATE: 0.90, Action.ENABLE_EXECUTION: 0.00})


class Supervisor:
    """Pure policy selector. It never mutates state or grants authority."""

    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()

    def safe_actions(self, state: EpistemicState) -> tuple[Action, ...]:
        s = state.normalized()
        if s.cycles:
            return (Action.REJECT, Action.QUARANTINE, Action.ESCALATE)
        safe = [Action.BLOCK, Action.BRANCH, Action.REJECT, Action.QUARANTINE, Action.ESCALATE, Action.ARCHIVE]
        execution_allowed = s.authority == Authority.EXECUTE and s.strain < self.config.u_crit and s.unsupported_depth < self.config.depth_bound and s.calibration_error < self.config.calibration_crit and s.active_branches <= self.config.branch_bound
        if execution_allowed:
            safe.append(Action.ENABLE_EXECUTION)
        return tuple(safe)

    def supervise(self, state: EpistemicState) -> Action:
        actions = self.safe_actions(state)
        return Action.ESCALATE if not actions else min(actions, key=lambda a: (self.config.cost_weights.get(a, 1.0), a.value))


class Transition:
    """The sole state mutation boundary for constitutional runtime state."""

    @staticmethod
    def apply(state: EpistemicState, action: Action, evidence: Sequence[EvidenceRecord] = ()) -> EpistemicState:
        s = state.normalized()
        evidence = tuple(evidence)
        next_authority = s.authority
        if action == Action.ENABLE_EXECUTION:
            next_authority = Authority.SIMULATE
        for record in evidence:
            if record.authority_grant is not None:
                requested = int(record.authority_grant)
                if requested > int(next_authority) and requested <= int(Authority.EXECUTE):
                    next_authority = Authority(min(int(next_authority) + 1, requested))
        return replace(s, authority=next_authority, evidence_count=s.evidence_count + len(evidence)).normalized()


def state_hash(state: EpistemicState) -> str:
    obj = {"observability": dict(sorted(state.observability.items())), "hypotheses": dict(sorted(state.hypotheses.items())), "predictions": {k: dict(sorted(v.items())) for k, v in sorted(state.predictions.items())}, "relevance": dict(sorted(state.relevance.items())), "strain": state.strain, "unsupported_depth": state.unsupported_depth, "critical_load": dict(sorted(state.critical_load.items())), "cycles": state.cycles, "authority": int(state.authority), "calibration_error": state.calibration_error, "active_branches": state.active_branches, "evidence_count": state.evidence_count, "policy_version": state.policy_version}
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
