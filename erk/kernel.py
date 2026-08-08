from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import hmac
import json
from typing import Mapping, Sequence

from .core import Action, Authority, EpistemicState, EvidenceRecord, PolicyConfig, Supervisor, Transition, _canonical, state_hash


class ConstitutionalViolation(RuntimeError):
    """Raised when a requested transition is not constitutionally admissible."""


@dataclass(frozen=True, slots=True)
class AuthorityKey:
    """Authenticated-key registry entry for the ERK authority boundary."""
    key_id: str
    secret: bytes
    valid_from: str = ""
    valid_until: str = ""
    revoked: bool = False

    def valid_for(self, timestamp: str) -> bool:
        if self.revoked:
            return False
        try:
            value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            if self.valid_from:
                start = datetime.fromisoformat(self.valid_from.replace("Z", "+00:00"))
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)
                if value < start:
                    return False
            if self.valid_until:
                end = datetime.fromisoformat(self.valid_until.replace("Z", "+00:00"))
                if end.tzinfo is None:
                    end = end.replace(tzinfo=timezone.utc)
                if value >= end:
                    return False
            return True
        except ValueError:
            return False


@dataclass(frozen=True, slots=True)
class KernelConfig:
    policy: PolicyConfig = field(default_factory=PolicyConfig)
    require_monotonic_evidence_count: bool = True
    authority_keys: Mapping[str, AuthorityKey] = field(default_factory=dict)
    branch_id: str = "main"


class ConstitutionalKernel:
    """Executable boundary between policy selection and state mutation."""

    def __init__(self, config: KernelConfig | None = None) -> None:
        self.config = config or KernelConfig()
        self.supervisor = Supervisor(self.config.policy)

    def admissible(self, state: EpistemicState, action: Action) -> bool:
        return action in self.supervisor.safe_actions(state)

    def _policy_hash(self) -> str:
        payload = {
            "u_crit": self.config.policy.u_crit,
            "depth_bound": self.config.policy.depth_bound,
            "calibration_crit": self.config.policy.calibration_crit,
            "branch_bound": self.config.policy.branch_bound,
            "cost_weights": {str(k): float(v) for k, v in self.config.policy.cost_weights.items()},
        }
        return hashlib.sha256(json.dumps(_canonical(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _grant_metadata(record: EvidenceRecord) -> tuple[str, str, str]:
        payload = dict(record.payload)
        key_id = str(payload.get("authority_key_id", record.source))
        nonce = str(payload.get("authority_nonce", record.authority_grant_id or ""))
        expires_at = str(payload.get("authority_expires_at", ""))
        return key_id, nonce, expires_at

    def _authority_binding(self, record: EvidenceRecord, state: EpistemicState) -> bytes:
        key_id, nonce, expires_at = self._grant_metadata(record)
        binding = {
            "prior_authority": int(state.authority),
            "target_authority": int(record.authority_grant) if record.authority_grant is not None else None,
            "evidence_hash": record.provenance_hash,
            "state_hash": state_hash(state),
            "policy_hash": self._policy_hash(),
            "branch_id": self.config.branch_id,
            "grant_id": record.authority_grant_id,
            "nonce": nonce,
            "key_id": key_id,
            "expires_at": expires_at,
        }
        return json.dumps(_canonical(binding), sort_keys=True, separators=(",", ":")).encode("utf-8")

    def _validate_evidence(self, state: EpistemicState, evidence: Sequence[EvidenceRecord]) -> Authority | None:
        requested: Authority | None = None
        seen_grant_ids: set[str] = set()
        seen_nonces: set[str] = set()
        for record in evidence:
            if record.authority_grant is None:
                continue
            if not record.authority_grant_id:
                raise ConstitutionalViolation("GRANT_ID_MISSING")
            if record.authority_grant_id in seen_grant_ids:
                raise ConstitutionalViolation("GRANT_REPLAY")
            if record.authority_grant_id in state.used_authority_grants:
                raise ConstitutionalViolation("GRANT_REPLAY")
            seen_grant_ids.add(record.authority_grant_id)

            key_id, nonce, expires_at = self._grant_metadata(record)
            if not nonce or nonce != record.authority_grant_id:
                raise ConstitutionalViolation("NONCE_MISMATCH")
            if nonce in seen_nonces:
                raise ConstitutionalViolation("NONCE_REPLAY")
            seen_nonces.add(nonce)
            if expires_at:
                try:
                    expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    issued = datetime.fromisoformat(record.timestamp.replace("Z", "+00:00"))
                    if expiry.tzinfo is None:
                        expiry = expiry.replace(tzinfo=timezone.utc)
                    if issued.tzinfo is None:
                        issued = issued.replace(tzinfo=timezone.utc)
                    if issued >= expiry:
                        raise ConstitutionalViolation("GRANT_EXPIRED")
                except ValueError as exc:
                    raise ConstitutionalViolation("GRANT_TIME_INVALID") from exc

            key = self.config.authority_keys.get(key_id)
            if key is None:
                raise ConstitutionalViolation("UNKNOWN_KEY")
            if not key.valid_for(record.timestamp):
                raise ConstitutionalViolation("KEY_REVOKED_OR_OUT_OF_VALIDITY")

            try:
                grant = Authority(int(record.authority_grant))
            except (ValueError, TypeError) as exc:
                raise ConstitutionalViolation("AUTHORITY_DOMAIN_INVALID") from exc
            if grant <= state.authority or grant != Authority(int(state.authority) + 1):
                raise ConstitutionalViolation("AUTHORITY_STEP_INVALID")

            expected = hmac.new(key.secret, self._authority_binding(record, state), hashlib.sha256).hexdigest()
            if not record.authority_signature or not hmac.compare_digest(expected, record.authority_signature):
                raise ConstitutionalViolation("BAD_SIGNATURE")

            if requested is not None and grant != requested:
                raise ConstitutionalViolation("MULTIPLE_GRANTS_DISAGREE")
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
            raise ConstitutionalViolation("EVIDENCE_COUNT_DECREASED")
        if action == Action.ENABLE_EXECUTION and after.authority >= Authority.EXECUTE:
            raise ConstitutionalViolation("EXECUTION_NOT_CONSUMED")
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
