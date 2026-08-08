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
    key_id: str
    signature: str


class ActuatorFirewall:
    """Final effect boundary: accepts only kernel-issued, one-use permits."""

    def __init__(self, kernel: ConstitutionalKernel, key_id: str) -> None:
        self.kernel = kernel
        self.key_id = key_id
        self._consumed: set[str] = set()

    def issue(self, state: EpistemicState) -> ExecutionPermit:
        if not self.kernel.admissible(state, Action.ENABLE_EXECUTION):
            raise ConstitutionalViolation("execution is not constitutionally admissible")
        if state.authority != Authority.EXECUTE:
            raise ConstitutionalViolation("execution permit requires EXECUTE authority")
        key = self.kernel.config.authority_keys.get(self.key_id)
        if key is None:
            raise ConstitutionalViolation("execution permit key unavailable")

        permit_id = secrets.token_hex(16)
        state_digest = self.kernel.replay_hash((state,))
        message = self._message(permit_id, state_digest, state.policy_version, Authority.EXECUTE, self.key_id)
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        return ExecutionPermit(permit_id, state_digest, state.policy_version, Authority.EXECUTE, self.key_id, signature)

    def execute(self, state: EpistemicState, permit: ExecutionPermit) -> None:
        if permit.permit_id in self._consumed:
            raise ConstitutionalViolation("execution permit replay detected")
        if state.authority != Authority.EXECUTE:
            raise ConstitutionalViolation("execution requires EXECUTE authority")
        if permit.authority != Authority.EXECUTE:
            raise ConstitutionalViolation("invalid execution permit authority")
        if permit.key_id != self.key_id:
            raise ConstitutionalViolation("execution permit key mismatch")
        if permit.policy_version != state.policy_version:
            raise ConstitutionalViolation("execution permit policy mismatch")
        if permit.state_hash != self.kernel.replay_hash((state,)):
            raise ConstitutionalViolation("execution permit state mismatch")

        key = self.kernel.config.authority_keys.get(self.key_id)
        if key is None:
            raise ConstitutionalViolation("execution permit key unavailable")
        expected = hmac.new(
            key,
            self._message(permit.permit_id, permit.state_hash, permit.policy_version, permit.authority, permit.key_id),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, permit.signature):
            raise ConstitutionalViolation("invalid execution permit signature")

        self._consumed.add(permit.permit_id)

    @staticmethod
    def _message(permit_id: str, state_hash: str, policy_version: str, authority: Authority, key_id: str) -> bytes:
        return f"{permit_id}|{state_hash}|{policy_version}|{int(authority)}|{key_id}".encode("utf-8")
