"""Sixteen additional regression/identification tests for the TIAMAT stack."""
from __future__ import annotations

import math

import pytest

from tiamat.adversarial_elimination import eliminate_winner
from tiamat.model_selection import CandidateSpec, ModelSelector, binary_auc, calibration_error
from tiamat.minimal_state import run_leave_one_out
from tiamat.tournament import TournamentCase, TournamentRunner

LABELS = (0, 1) * 8
GOOD = tuple(0.10 if y == 0 else 0.90 for y in LABELS)
WEAK = tuple(0.45 if y == 0 else 0.55 for y in LABELS)
NEUTRAL = (0.50,) * len(LABELS)
INVERSE = tuple(0.90 if y == 0 else 0.10 for y in LABELS)


def _case(specs, predictions, *, max_size=2):
    return TournamentCase(
        name="extended",
        labels=LABELS,
        heldout_predictions=predictions,
        max_size=max_size,
        specs=tuple(specs),
    )


def test_01_auc_perfect_signal() -> None:
    assert binary_auc(GOOD, LABELS) == 1.0


def test_02_auc_inverse_signal() -> None:
    assert binary_auc(INVERSE, LABELS) == 0.0


def test_03_calibration_error_is_bounded() -> None:
    assert 0.0 <= calibration_error(GOOD, LABELS) <= 1.0


def test_04_neutral_control_is_unresolved() -> None:
    specs = (CandidateSpec("neutral", ("neutral",)),)
    result = TournamentRunner(specs=specs).run_case(_case(specs, {"neutral": NEUTRAL}))
    assert result.decision.status == "UNRESOLVED"
    assert result.decision.selected_model_id is None


def test_05_clean_signal_is_selected() -> None:
    specs = (CandidateSpec("signal", ("state",)), CandidateSpec("neutral", ("neutral",)))
    result = TournamentRunner(specs=specs).run_case(_case(specs, {"signal": GOOD, "neutral": NEUTRAL}))
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "signal"


def test_06_inverse_signal_cannot_win() -> None:
    specs = (CandidateSpec("inverse", ("inverse",)), CandidateSpec("neutral", ("neutral",)))
    result = TournamentRunner(specs=specs).run_case(_case(specs, {"inverse": INVERSE, "neutral": NEUTRAL}))
    assert result.decision.status == "UNRESOLVED"


def test_07_weak_signal_beats_neutral_when_gate_allows() -> None:
    # This test intentionally isolates the weak-signal gate from calibration.
    # The canonical selector keeps ECE <= .10; WEAK has ECE=.45 by construction.
    selector = ModelSelector(min_brier_skill=-1.0, max_calibration_error=0.50)
    specs = (CandidateSpec("weak", ("weak",)), CandidateSpec("neutral", ("neutral",)))
    result = TournamentRunner(selector=selector, specs=specs).run_case(_case(specs, {"weak": WEAK, "neutral": NEUTRAL}))
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "weak"


def test_08_interaction_candidate_can_win() -> None:
    specs = (
        CandidateSpec("a", ("a",)),
        CandidateSpec("b", ("b",)),
        CandidateSpec("a_b", ("a", "b")),
    )
    result = TournamentRunner(specs=specs).run_case(
        _case(specs, {"a": NEUTRAL, "b": NEUTRAL, "a_b": GOOD})
    )
    assert result.decision.selected_model_id == "a_b"


def test_09_explicit_candidate_vocabulary_is_preserved() -> None:
    specs = (CandidateSpec("probe_x", ("x",)), CandidateSpec("probe_y", ("y",)))
    case = _case(specs, {"probe_x": GOOD, "probe_y": NEUTRAL})
    result = TournamentRunner().run_case(case)
    assert result.best_model_id == "probe_x"
    assert {r.spec.model_id for r in result.report.evaluated} == {"probe_x", "probe_y"}


def test_10_tournament_is_deterministic() -> None:
    specs = (CandidateSpec("signal", ("state",)), CandidateSpec("neutral", ("neutral",)))
    case = _case(specs, {"signal": GOOD, "neutral": NEUTRAL})
    runner = TournamentRunner(specs=specs)
    a = runner.run_case(case)
    b = runner.run_case(case)
    assert a == b


def test_11_ablation_identifies_dependency_change() -> None:
    specs = (
        CandidateSpec("core", ("damage", "momentum")),
        CandidateSpec("damage_only", ("damage",)),
        CandidateSpec("neutral", ("neutral",)),
    )
    rows = run_leave_one_out(
        labels=LABELS,
        specs=specs,
        predictions={"core": GOOD, "damage_only": GOOD, "neutral": NEUTRAL},
        max_size=2,
    )
    by_feature = {row.feature: row for row in rows}
    assert by_feature["damage"].classification == "ESSENTIAL"
    assert by_feature["momentum"].classification == "REDUNDANT"
    assert by_feature["neutral"].classification == "REDUNDANT"


def test_12_winner_elimination_has_an_observed_failure() -> None:
    specs = (CandidateSpec("winner", ("state",)), CandidateSpec("neutral", ("neutral",)))
    result = eliminate_winner(
        labels=LABELS,
        specs=specs,
        predictions={"winner": GOOD, "neutral": NEUTRAL},
        winner="winner",
        max_size=1,
    )
    assert result.failed
    assert set(result.survived).isdisjoint(result.failed)


def test_13_ablation_never_invents_a_prediction_stream() -> None:
    specs = (CandidateSpec("signal", ("state",)), CandidateSpec("neutral", ("neutral",)))
    result = run_leave_one_out(labels=LABELS, specs=specs, predictions={"signal": GOOD}, max_size=1)
    assert result
    assert all(row.baseline_selected == "signal" for row in result)


def test_14_probabilities_remain_in_unit_interval() -> None:
    for value in GOOD + WEAK + NEUTRAL + INVERSE:
        assert 0.0 <= value <= 1.0
        assert math.isfinite(value)


def test_15_model_selector_rejects_empty_evidence() -> None:
    decision = ModelSelector().select(())
    assert decision.status == "UNRESOLVED"
    assert decision.selected_model_id is None


def test_16_duplicate_candidate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="candidate model IDs must be unique"):
        TournamentCase(
            name="duplicate",
            labels=LABELS,
            heldout_predictions={"x": GOOD},
            specs=(CandidateSpec("x", ("a",)), CandidateSpec("x", ("b",))),
        )
