from __future__ import annotations

import math

import pytest

from tiamat.engine import TiamatEngine
from tiamat.modes import TiamatMode
from tiamat.state import TiamatState


def test_engine_step_and_replay() -> None:
    engine = TiamatEngine()
    initial = TiamatState(B=0.0, V=1.0, D=0.0)
    evidence = (
        {"V": 0.1},
        {"V": 0.1, "B": 0.2},
        {"D": 0.9, "damage_threshold": 0.8},
    )
    state = initial
    for row in evidence:
        state = engine.step(state, row)
    assert engine.replay_state(initial, evidence) == state
    assert math.isfinite(state.residual_load)


def test_diagnose_accepts_canonical_state_for_matched_damage_pokes() -> None:
    engine = TiamatEngine()
    # D is deliberately omitted from evidence: transition() treats an evidence
    # D as the next observed D and would overwrite the state-only perturbation.
    evidence = {"B": 0.0, "V": 1.0}
    for damage in (0.0, 1e-9, 1e-6):
        state = TiamatState(B=0.0, V=1.0, D=damage)
        diagnostic = engine.diagnose(state, evidence)
        assert diagnostic["state"]["D"] == damage
        assert diagnostic["state"]["V"] == 1.0
        assert diagnostic["state"]["B"] == 0.0


def test_engine_exposes_canonical_modes() -> None:
    assert tuple(TiamatMode) == (
        TiamatMode.QUIESCENT,
        TiamatMode.PRECURSOR,
        TiamatMode.EXCITATION,
        TiamatMode.COUPLED_TRANSFER,
        TiamatMode.HAZARD,
        TiamatMode.RELAXATION,
        TiamatMode.REFRACTORY,
    )


def test_engine_diagnose_returns_guard_and_observable_projection() -> None:
    engine = TiamatEngine()
    state = TiamatState(B=0.0, V=1.0, D=0.2)
    diagnostic = engine.diagnose(state, {"B": 0.0, "V": 1.0})
    assert "guards" in diagnostic
    assert "observables" in diagnostic
    assert set(("recovery", "pressure", "momentum", "residual_load", "hazard_raw", "hazard_score")) <= set(diagnostic["observables"])


def test_engine_evaluate_legacy_permission_path() -> None:
    engine = TiamatEngine()
    decision = engine.evaluate({"x": 1}, {"y": 2})
    assert decision.approved is True
    assert decision.state == {"x": 1, "y": 2}


def test_engine_rejects_disallowed_legacy_request() -> None:
    engine = TiamatEngine()
    decision = engine.evaluate({"x": 1}, {"allow": False})
    assert decision.approved is False
    assert decision.reason == "request disallowed"
