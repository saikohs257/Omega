from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import secrets
from typing import Callable

from .core import Action, Authority, EpistemicState
from .kernel import ConstitutionalKernel, ConstitutionalViolation


@dataclass(frozen=True, slots=True)
class ExecutionPermit:
    permit_id: str
    effect_id: str
    state_hash: str
    policy_version: str
    authority: Authority
    key_id: str
    signature: str


@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    permit_id: str
    effect_id: str
    committed: bool


class ActuatorFirewall:
    """Final effect boundary with explicit prepare/commit semantics.

    The firewall authenticates authorization and supplies a stable effect_id
    so an external actuator can implement idempotent effects. Exactly-once
    external execution requires the actuator/effect store to atomically bind
    effect_id to the external effect; the firewall alone cannot guarantee that.
    """

    def __init__(self, kernel: ConstitutionalKernel, key_id: str) -> None:
        self.kernel = kernel
        self.key_id = key_id
        self._prepared: dict[str, ExecutionPermit] = {}
        self._consumed: set[str] = set()

    def issue(self, state: EpistemicState, effect_id: str | None = None) -> ExecutionPermit:
        if not self.kernel.admissible(state, Action.ENABLE_EXECUTION):
            raise ConstitutionalViolation("execution is not constitutionally admissible")
        if state.authority != Authority.EXECUTE:
            raise ConstitutionalViolation("execution permit requires EXECUTE authority")
        key = self.kernel.config.authority_keys.get(self.key_id)
        if key is None:
            raise ConstitutionalViolation("execution permit key unavailable")
        effect_id = effect_id or secrets.token_hex(16)
        state_digest = self.kernel.replay_hash((state,))
        permit_id = secrets.token_hex(16)
        message = self._message(permit_id, effect_id, state_digest, state.policy_version, Authority.EXECUTE, self.key_id)
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()
        return ExecutionPermit(permit_id, effect_id, state_digest, state.policy_version, Authority.EXECUTE, self.key_id, signature)

    def prepare(self, state: EpistemicState, permit: ExecutionPermit) -> str:
        self._verify(state, permit)
        if permit.permit_id in self._consumed:
            raise ConstitutionalViolation("execution permit replay detected")
        existing = self._prepared.get(permit.permit_id)
        if existing is not None and existing != permit:
            raise ConstitutionalViolation("execution permit substitution detected")
        self._prepared[permit.permit_id] = permit
        return permit.effect_id

    def commit(self, permit: ExecutionPermit, effect: Callable[[str], None]) -> ExecutionReceipt:
        if permit.permit_id in self._consumed:
            raise ConstitutionalViolation("execution permit replay detected")
        prepared = self._prepared.get(permit.permit_id)
        if prepared != permit:
            raise ConstitutionalViolation("execution permit was not prepared")
        effect(permit.effect_id)
        self._consumed.add(permit.permit_id)
        self._prepared.pop(permit.permit_id, None)
        return ExecutionReceipt(permit.permit_id, permit.effect_id, True)

    def execute(self, state: EpistemicState, permit: ExecutionPermit, effect: Callable[[str], None]) -> ExecutionReceipt:
        self.prepare(state, permit)
        return self.commit(permit, effect)

    def _verify(self, state: EpistemicState, permit: ExecutionPermit) -> None:
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
            self._message(permit.permit_id, permit.effect_id, permit.state_hash, permit.policy_version, permit.authority, permit.key_id),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, permit.signature):
            raise ConstitutionalViolation("invalid execution permit signature")

    @staticmethod
    def _message(permit_id: str, effect_id: str, state_hash: str, policy_version: str, authority: Authority, key_id: str) -> bytes:
        return f"{permit_id}|{effect_id}|{state_hash}|{policy_version}|{int(authority)}|{key_id}".encode("utf-8")
