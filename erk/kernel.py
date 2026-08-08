from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import hmac
import json
from typing import Mapping, Sequence

from .core import Action, Authority, EpistemicState, EvidenceRecord, PolicyConfig, Supervisor, Transition, _canonical


class ConstitutionalViolation(RuntimeError):
    """Raised when a requested transition is not constitutionally admissible."""


@dataclass(frozen=True, slots=True)
class KernelConfig:
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    require_monotonic_evidence_count: bool = True
    authority_keys: Mapping[str, bytes] = field(default_factory=dict)


class ConstitutionalKernel:
    """Executable boundary between policy selection and state mutation."""

    def __init__(self, config: KernelConfig | None = None) -> None:
        self.config = config or KernelConfig()
        self.supervisor = Supervisor(self.config.policy)

    def admissible(self, state: EpistemicState, action: Action) -> bool:
        return action in self.supervisor.safe_actions(state)

    @staticmethod
    def _authority_binding(record: EvidenceRecord, state: EpistemicState) -> bytes:
        binding = {"base_authority": int(state.authority), "evidence_count": state.evidence_count}
        return record.authority_message(state) + b"|" + json.dumps(_canonical(binding), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _validate_evidence(self, state: EpistemicState, evidence: Sequence[EvidenceRecord]) -> Authority | None:
        requested: Authority | None = None
        seen_grant_ids: set[str] = set()
        for record in evidence:
            if record.authority_grant is None:
                continue
            if not record.authority_grant_id:
                raise ConstitutionalViolation("authority grant requires unique grant id")
            if record.authority_grant_id in seen_grant_ids:
                raise ConstitutionalViolation("duplicate authority grant id in transition")
            if record.authority_grant_id in state.used_authority_grants:
                raise ConstitutionalViolation("authority grant replay detected")
            seen_grant_ids.add(record.authority_grant_id)
            try:
                grant = Authority(int(record.authority_grant))
            except (ValueError, TypeError) as exc:
                raise ConstitutionalViolation("authority grant outside constitutional domain") from exc
            key = self.config.authority_keys.get(record.source)
            if key is None:
                raise ConstitutionalViolation("untrusted source attempted authority escalation")
            expected = hmac.new(key, self._authority_binding(record, state), hashlib.sha256).hexdigest()
            if not record.authority_signature or not hmac.compare_digest(expected, record.authority_signature):
                raise ConstitutionalViolation("invalid authority signature")
            if grant <= state.authority or grant != Authority(int(state.authority) + 1):
                raise ConstitutionalViolation("authority escalation must be exactly one level")
            if requested is not None and grant != requested:
                raise ConstitutionalViolation("multiple authority grants disagree")
            requested = grant
        return requested

    def step(self, state: EpistemicState, action: Action, evidence: Sequence[EvidenceRecord] = ()) -> EpistemicState:
        before = state.normalized()
        evidence = tuple(evidence)
        authorized_grant = self._validate_evidence(before, evidence)
        if not self.admissible(before, action):
            raise ConstitutionalViolation(f"inadmissible action: {action}")
        after = Transition.apply(
            before, action, evidence,
            authorized_authority=authorized_grant,
            branch_bound=self.config.policy.branch_bound,
            _kernel_authorized=True,
        )
        if self.config.require_monotonic_evidence_count and after.evidence_count < before.evidence_count:
            raise ConstitutionalViolation("evidence count decreased")
        if action == Action.ENABLE_EXECUTION and after.authority >= Authority.EXECUTE:
            raise ConstitutionalViolation("execution failed to consume authority")
        return after

    def replay(self, initial: EpistemicState, events: Sequence[tuple[Action, Sequence[EvidenceRecord]]]) -> tuple[EpistemicState, ...]:
        states = [initial.normalized()]
        current = states[0]
        for action, evidence in events:
            current = self.step(current, action, evidence)
            states.append(current)
        return tuple(states)

    @staticmethod
    def replay_hash(states: Sequence[EpistemicState]) -> str:
        payload = [_canonical({"observability": dict(state.observability), "hypotheses": dict(state.hypotheses), "predictions": dict(state.predictions), "relevance": dict(state.relevance), "strain": state.strain, "unsupported_depth": state.unsupported_depth, "critical_load": dict(state.critical_load), "cycles": state.cycles, "authority": int(state.authority), "calibration_error": state.calibration_error, "active_branches": state.active_branches, "evidence_count": state.evidence_count, "policy_version": state.policy_version, "terminal": state.terminal, "used_authority_grants": state.used_authority_grants}) for state in states]
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
