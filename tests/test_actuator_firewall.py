from __future__ import annotations

import pytest

from erk.actuator import ActuatorFirewall
from erk.core import Action, Authority, EpistemicState
from erk.kernel import ConstitutionalKernel, ConstitutionalViolation, KernelConfig

KEY = b"execution-test-key"
SOURCE = "trusted"


def kernel() -> ConstitutionalKernel:
    return ConstitutionalKernel(KernelConfig(authority_keys={SOURCE: KEY}))


def executable_state() -> EpistemicState:
    return EpistemicState(authority=Authority.EXECUTE)


def test_permit_requires_execution_admissibility() -> None:
    firewall = ActuatorFirewall(kernel(), SOURCE)
    with pytest.raises(ConstitutionalViolation, match="admissible"):
        firewall.issue(EpistemicState(authority=Authority.SIMULATE))


def test_valid_permit_reaches_final_firewall_once() -> None:
    firewall = ActuatorFirewall(kernel(), SOURCE)
    state = executable_state()
    permit = firewall.issue(state)
    effects: list[str] = []
    firewall.execute(state, permit, effects.append)
    assert effects == [permit.effect_id]
    with pytest.raises(ConstitutionalViolation, match="replay"):
        firewall.execute(state, permit, effects.append)
    assert effects == [permit.effect_id]


def test_commit_rechecks_current_state_after_prepare() -> None:
    firewall = ActuatorFirewall(kernel(), SOURCE)
    state = executable_state()
    permit = firewall.issue(state)
    firewall.prepare(state, permit)
    changed = EpistemicState(authority=Authority.SIMULATE)
    effects: list[str] = []
    with pytest.raises(ConstitutionalViolation, match="EXECUTE"):
        firewall.commit(changed, permit, effects.append)
    assert effects == []


def test_commit_rechecks_policy_after_prepare() -> None:
    firewall = ActuatorFirewall(kernel(), SOURCE)
    state = executable_state()
    permit = firewall.issue(state)
    firewall.prepare(state, permit)
    changed = EpistemicState(authority=Authority.EXECUTE, policy_version="changed-policy")
    effects: list[str] = []
    with pytest.raises(ConstitutionalViolation, match="policy mismatch"):
        firewall.commit(changed, permit, effects.append)
    assert effects == []


def test_permit_cannot_cross_state_boundary() -> None:
    firewall = ActuatorFirewall(kernel(), SOURCE)
    permit = firewall.issue(executable_state())
    changed = EpistemicState(authority=Authority.EXECUTE, policy_version="different")
    with pytest.raises(ConstitutionalViolation, match="policy mismatch"):
        firewall.execute(changed, permit, lambda _: None)


def test_permit_cannot_cross_key_boundary() -> None:
    issuing = ActuatorFirewall(kernel(), SOURCE)
    permit = issuing.issue(executable_state())
    other = ActuatorFirewall(kernel(), "other")
    with pytest.raises(ConstitutionalViolation, match="key mismatch"):
        other.execute(executable_state(), permit, lambda _: None)


def test_execution_transition_consumes_authority_after_permit() -> None:
    k = kernel()
    state = executable_state()
    firewall = ActuatorFirewall(k, SOURCE)
    permit = firewall.issue(state)
    firewall.execute(state, permit, lambda _: None)
    after = k.step(state, Action.ENABLE_EXECUTION)
    assert after.authority == Authority.SIMULATE
