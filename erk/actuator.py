from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import secrets

from .core import Action, Authority, EpistemicState
from .kernel import ConstitutionalKernel, ConstitutionalViolation


@dataclass(frozen=True, slots=True)
class ExecutionPermit:
    permit_id: str
    state_hash: str
    policy_version: str
    authority: Authority
    signature: str


class ActuatorFirewall:
    """Final effect boundary: accepts only kernel-issued, one-use permits."""

    def __init__(self, kernel: ConstitutionalKernel) -> None:
        self.kernel = kernel
        self._consumed: set[str] = set()

    def issue(self, state: EpistemicState) -> ExecutionPermit:
        if not self.kernel.admissible(state, Action.ENABLE_EXECUTION):
            raise ConstitutionalViolation("execution is not constitutionally admissible")
        if state.authority != Authority.EXECUTE:
            raise ConstitutionalViolation("execution permit requires EXECUTE authority")

        permit_id = secrets.token_hex(16)
        state_digest = self.kernel.replay_hash((state,))
        message = f"{permit_id}|{state_digest}|{state.policy_version}|{int(state.authority)}".encode()
        key = self._permit_key()
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        return ExecutionPermit(
            permit_id=permit_id,
            state_hash=state_digest,
            policy_version=state.policy_version,
            authority=state.authority,
            signature=signature,
        )

    def execute(self, state: EpistemicState, permit: ExecutionPermit) -> None:
        if permit.permit_id in self._consumed:
            raise ConstitutionalViolation("execution permit replay detected")
        if state.authority != Authority.EXECUTE:
            raise ConstitutionalViolation("execution requires EXECUTE authority")
        if permit.authority != Authority.EXECUTE:
            raise ConstitutionalViolation("invalid execution permit authority")
        if permit.policy_version != state.policy_version:
            raise ConstitutionalViolation("execution permit policy mismatch")
        if permit.state_hash != self.kernel.replay_hash((state,)):
            raise ConstitutionalViolation("execution permit state mismatch")

        message = f"{permit.permit_id}|{permit.state_hash}|{permit.policy_version}|{int(permit.authority)}".encode()
        expected = hmac.new(self._permit_key(), message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, permit.signature):
            raise ConstitutionalViolation("invalid execution permit signature")

        self._consumed.add(permit.permit_id)

    def _permit_key(self) -> bytes:
        keys = self.kernel.config.authority_keys
        if not keys:
            raise ConstitutionalViolation("execution permit key unavailable")
        return next(iter(keys.values()))
