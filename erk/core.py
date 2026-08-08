from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import IntEnum, StrEnum
import hashlib
import hmac
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
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)
    return value


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(item) for item in value), key=repr)
    return value


def _prediction_distance(first: Any, second: Any) -> float:
    if isinstance(first, (int, float)) and isinstance(second, (int, float)):
        return min(1.0, abs(float(first) - float(second)))
    return 0.0 if first == second else 1.0


def _finite_nonnegative(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def compute_strain(hypotheses: Mapping[str, float], predictions: Mapping[str, Mapping[str, Any]], observability: Mapping[str, float], relevance: Mapping[str, float] | None = None, lam: float = 1.0) -> float:
    lam = _finite_nonnegative(lam, "lam")
    if not hypotheses:
        return 0.0
    total = sum(max(0.0, float(probability)) for probability in hypotheses.values())
    if total <= 0:
        return 0.0
    probabilities = {name: max(0.0, float(probability)) / total for name, probability in hypotheses.items()}
    relevance = relevance or {}
    names = list(probabilities)
    conflict = 0.0
    for index, first in enumerate(names):
        for second in names[index + 1:]:
            disagreement = sum(
                max(0.0, float(relevance.get(variable, 1.0)))
                * float(observed)
                * _prediction_distance(predictions.get(first, {}).get(variable), predictions.get(second, {}).get(variable))
                for variable, observed in observability.items()
                if observed > 0
            )
            conflict += probabilities[first] * probabilities[second] * disagreement
    return 1.0 - math.exp(-lam * max(0.0, conflict))


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: str
    source: str
    timestamp: str
    payload: Mapping[str, Any]
    authority_grant: int | None = None
    authority_signature: str = ""
    provenance_hash: str = ""
    authority_grant_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze(self.payload))
        digest = hashlib.sha256(self._canonical_content()).hexdigest()
        if self.provenance_hash and self.provenance_hash != digest:
            raise ValueError("provenance_hash does not match immutable evidence")
        object.__setattr__(self, "provenance_hash", digest)

    def _content(self, include_signature: bool = True) -> dict[str, Any]:
        return {"evidence_id": self.evidence_id, "source": self.source, "timestamp": self.timestamp, "payload": _canonical(self.payload), "authority_grant": self.authority_grant, "authority_grant_id": self.authority_grant_id, "authority_signature": self.authority_signature if include_signature else ""}

    def _canonical_content(self) -> bytes:
        return json.dumps(self._content(), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")

    def authority_message(self, state: EpistemicState) -> bytes:
        binding = {"base_authority": int(state.authority), "evidence_count": state.evidence_count, "policy_version": state.policy_version, "state_hash": state_hash(state)}
        return json.dumps({"evidence": self._content(False), "binding": _canonical(binding)}, sort_keys=True, separators=(",", ":")).encode("utf-8")


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
    ids = {node.node_id for node in nodes}
    adjacency: dict[str, list[str]] = {node_id: [] for node_id in ids}
    for edge in edges:
        if edge.kind == "DEPENDS_ON" and edge.source in ids and edge.target in ids:
            adjacency[edge.source].append(edge.target)
    cycles: list[tuple[str, ...]] = []
    color = {node_id: 0 for node_id in ids}
    stack: list[str] = []
    def visit(node_id: str) -> None:
        color[node_id] = 1
        stack.append(node_id)
        for target in adjacency[node_id]:
            if color[target] == 0:
                visit(target)
            elif color[target] == 1:
                start = stack.index(target)
                cycles.append(tuple(stack[start:] + [target]))
        stack.pop()
        color[node_id] = 2
    for node_id in sorted(ids):
        if color[node_id] == 0:
            visit(node_id)
    memo: dict[str, int] = {}
    def depth(node_id: str, visiting: set[str]) -> int:
        if node_id in memo:
            return memo[node_id]
        if node_id in visiting:
            return 0
        visiting.add(node_id)
        value = max((1 + depth(target, visiting) for target in adjacency[node_id]), default=0)
        visiting.remove(node_id)
        memo[node_id] = value
        return value
    critical: dict[str, int] = {}
    for node_id in sorted(ids):
        seen: set[str] = set()
        todo = list(adjacency[node_id])
        while todo:
            target = todo.pop()
            if target in seen:
                continue
            seen.add(target)
            todo.extend(adjacency[target])
        critical[node_id] = len(seen)
    unsupported = [node.node_id for node in nodes if not node.supported]
    return GraphMetrics(max((depth(node_id, set()) for node_id in unsupported), default=0), MappingProxyType(critical), tuple(cycles))


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
    terminal: str | None = None
    used_authority_grants: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("observability", "hypotheses", "predictions", "relevance", "critical_load"):
            object.__setattr__(self, name, _freeze(getattr(self, name)))
        object.__setattr__(self, "used_authority_grants", tuple(self.used_authority_grants))

    def normalized(self) -> EpistemicState:
        return replace(self, observability={key: min(1.0, max(0.0, float(value))) for key, value in self.observability.items()}, strain=min(1.0, max(0.0, float(self.strain))), calibration_error=min(1.0, max(0.0, float(self.calibration_error))), active_branches=max(0, int(self.active_branches)), evidence_count=max(0, int(self.evidence_count)), used_authority_grants=tuple(self.used_authority_grants))


@dataclass(frozen=True, slots=True)
class PolicyConfig:
    u_crit: float = 0.80
    depth_bound: int = 8
    calibration_crit: float = 0.25
    branch_bound: int = 16
    cost_weights: Mapping[Action, float] = field(default_factory=lambda: {Action.BLOCK: 0.20, Action.BRANCH: 0.40, Action.ARCHIVE: 0.60, Action.QUARANTINE: 0.80, Action.REJECT: 1.00, Action.ESCALATE: 0.90, Action.ENABLE_EXECUTION: 0.00})
    def __post_init__(self) -> None:
        object.__setattr__(self, "cost_weights", _freeze(self.cost_weights))


class Supervisor:
    """Deterministic constitutional policy layer. Safety gates precede optimization."""
    def __init__(self, config: PolicyConfig | None = None) -> None:
        self.config = config or PolicyConfig()
    def safe_actions(self, state: EpistemicState) -> tuple[Action, ...]:
        state = state.normalized()
        if state.terminal is not None: return ()
        if state.cycles: return (Action.REJECT, Action.QUARANTINE, Action.ESCALATE)
        if state.strain >= self.config.u_crit: return (Action.QUARANTINE, Action.REJECT, Action.ESCALATE)
        if state.calibration_error >= self.config.calibration_crit: return (Action.ESCALATE, Action.QUARANTINE)
        if state.unsupported_depth >= self.config.depth_bound: return (Action.ESCALATE, Action.QUARANTINE)
        if state.active_branches >= self.config.branch_bound: return (Action.BLOCK, Action.ESCALATE, Action.QUARANTINE)
        actions = [Action.BLOCK, Action.BRANCH, Action.REJECT, Action.QUARANTINE, Action.ESCALATE, Action.ARCHIVE]
        if state.authority == Authority.EXECUTE: actions.append(Action.ENABLE_EXECUTION)
        return tuple(actions)
    def supervise(self, state: EpistemicState) -> Action:
        state = state.normalized(); actions = self.safe_actions(state)
        if not actions: return Action.ESCALATE
        if state.cycles: return Action.REJECT
        if state.strain >= self.config.u_crit: return Action.QUARANTINE
        if state.calibration_error >= self.config.calibration_crit: return Action.ESCALATE
        if state.unsupported_depth >= self.config.depth_bound: return Action.ESCALATE
        if state.active_branches >= self.config.branch_bound: return Action.BLOCK
        if state.authority == Authority.EXECUTE: return Action.ENABLE_EXECUTION
        preferred = (Action.BLOCK, Action.BRANCH, Action.ARCHIVE, Action.QUARANTINE, Action.REJECT, Action.ESCALATE)
        admissible = set(actions)
        for action in preferred:
            if action in admissible: return action
        return min(actions, key=lambda action: (self.config.cost_weights.get(action, 1.0), action.value))


class Transition:
    @staticmethod
    def apply(state: EpistemicState, action: Action, evidence: Sequence[EvidenceRecord] = (), authorized_authority: Authority | None = None, branch_bound: int = 16, *, _kernel_authorized: bool = False) -> EpistemicState:
        state = state.normalized(); evidence = tuple(evidence)
        if state.terminal is not None: raise ValueError("terminal branch cannot transition")
        if branch_bound < 1: raise ValueError("branch bound must be positive")
        if authorized_authority is not None and not _kernel_authorized: raise ValueError("authority escalation requires kernel authorization")
        grant_ids = tuple(record.authority_grant_id for record in evidence if record.authority_grant is not None and record.authority_grant_id is not None)
        if len(set(grant_ids)) != len(grant_ids): raise ValueError("duplicate authority grant id in transition")
        if any(grant_id in state.used_authority_grants for grant_id in grant_ids): raise ValueError("authority grant replay detected")
        if action == Action.BRANCH:
            if state.active_branches >= branch_bound: raise ValueError("branch bound exceeded")
            return replace(state, active_branches=state.active_branches + 1, evidence_count=state.evidence_count + len(evidence), used_authority_grants=state.used_authority_grants + grant_ids).normalized()
        if action in (Action.REJECT, Action.QUARANTINE, Action.ARCHIVE):
            return replace(state, terminal=action.value, evidence_count=state.evidence_count + len(evidence), used_authority_grants=state.used_authority_grants + grant_ids).normalized()
        if action == Action.ENABLE_EXECUTION:
            if state.authority != Authority.EXECUTE: raise ValueError("execution requires authority=EXECUTE")
            return replace(state, authority=Authority.SIMULATE, evidence_count=state.evidence_count + len(evidence), used_authority_grants=state.used_authority_grants + grant_ids).normalized()
        next_authority = state.authority
        if authorized_authority is not None:
            expected = Authority(int(state.authority) + 1)
            if authorized_authority != expected: raise ValueError("authority escalation must be exactly one level")
            next_authority = authorized_authority
        return replace(state, authority=next_authority, evidence_count=state.evidence_count + len(evidence), used_authority_grants=state.used_authority_grants + grant_ids).normalized()


def state_hash(state: EpistemicState) -> str:
    payload = {"observability": dict(state.observability), "hypotheses": dict(state.hypotheses), "predictions": dict(state.predictions), "relevance": dict(state.relevance), "strain": state.strain, "unsupported_depth": state.unsupported_depth, "critical_load": dict(state.critical_load), "cycles": state.cycles, "authority": int(state.authority), "calibration_error": state.calibration_error, "active_branches": state.active_branches, "evidence_count": state.evidence_count, "policy_version": state.policy_version, "terminal": state.terminal, "used_authority_grants": state.used_authority_grants}
    return hashlib.sha256(json.dumps(_canonical(payload), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
