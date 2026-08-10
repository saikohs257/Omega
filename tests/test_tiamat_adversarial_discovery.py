"""Adversarial discovery tests for TIAMAT candidate selection.

These cases stress the evidence machinery against deceptive but plausible
candidate predictions. They intentionally use opaque model IDs so the selector
cannot rely on semantic names.
"""
from __future__ import annotations

from tiamat.model_selection import CandidateSpec, ModelSelector
from tiamat.tournament import TournamentCase, TournamentRunner

LABELS = (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1)
GOOD = tuple(0.15 if y == 0 else 0.85 for y in LABELS)
MEDIUM = tuple(0.35 if y == 0 else 0.65 for y in LABELS)
NEUTRAL = tuple(0.50 for _ in LABELS)


def run(predictions: dict[str, tuple[float, ...]], specs: tuple[CandidateSpec, ...] | None = None,
        *, min_auc: float = 0.60, max_brier: float = 0.25,
        max_calibration_error: float = 1.0) -> object:
    specs = specs or tuple(CandidateSpec(name, (name,)) for name in predictions)
    selector = ModelSelector(
        min_auc=min_auc,
        max_brier=max_brier,
        max_calibration_error=max_calibration_error,
    )
    return TournamentRunner(specs=specs, selector=selector).run_case(
        TournamentCase(name="adversarial", labels=LABELS, heldout_predictions=predictions, max_size=4)
    )


def test_delayed_signal_does_not_reward_a_wrong_instantaneous_proxy() -> None:
    delayed = tuple(0.20 if y == 0 else 0.80 for y in LABELS)
    proxy = tuple(0.48 if y == 0 else 0.52 for y in LABELS)
    result = run({"opaque_a": delayed, "opaque_b": proxy})
    assert result.decision.selected_model_id == "opaque_a"


def test_small_complexity_wins_when_evidence_is_equivalent() -> None:
    specs = (
        CandidateSpec("one", ("x",)),
        CandidateSpec("three", ("a", "b", "c")),
        CandidateSpec("five", ("a", "b", "c", "d", "e")),
    )
    result = run({"one": GOOD, "three": GOOD, "five": GOOD}, specs)
    assert result.decision.selected_model_id == "one"


def test_redundant_high_score_does_not_require_giant_context() -> None:
    specs = (
        CandidateSpec("compact", ("x", "y")),
        CandidateSpec("giant", tuple(f"f{i}" for i in range(12))),
    )
    result = run({"compact": GOOD, "giant": GOOD}, specs)
    assert result.decision.selected_model_id == "compact"


def test_conflicting_models_surface_a_contested_frontier() -> None:
    a = GOOD
    b = tuple(0.85 if y == 0 else 0.15 for y in LABELS)
    result = run({"a": a, "b": b})
    assert result.decision.status == "SELECTED"
    assert result.report.frontier


def test_no_signal_with_tiny_noise_stays_unresolved() -> None:
    noisy = tuple(0.49 + (0.01 if i % 2 else -0.01) for i in range(len(LABELS)))
    result = run({"noise": noisy}, min_auc=0.60)
    assert result.decision.status == "UNRESOLVED"


def test_boundary_auc_is_not_promoted() -> None:
    boundary = tuple(0.49 if y == 0 else 0.51 for y in LABELS)
    result = run({"boundary": boundary}, min_auc=0.99)
    assert result.decision.status == "UNRESOLVED"


def test_interaction_model_beats_neutral_singletons() -> None:
    specs = (
        CandidateSpec("left", ("left",)),
        CandidateSpec("right", ("right",)),
        CandidateSpec("joint", ("left", "right")),
    )
    result = run({"left": NEUTRAL, "right": NEUTRAL, "joint": GOOD}, specs)
    assert result.decision.selected_model_id == "joint"


def test_calibration_gate_rejects_rank_correct_but_miscalibrated_model() -> None:
    specs = (
        CandidateSpec("cal", ("cal",)),
        CandidateSpec("badcal", ("badcal",)),
    )
    badcal = tuple(0.49 if y == 0 else 0.99 for y in LABELS)
    result = run({"cal": MEDIUM, "badcal": badcal}, specs, max_calibration_error=0.10)
    assert result.decision.selected_model_id == "cal"


def test_all_candidates_can_fail_without_forced_selection() -> None:
    specs = (
        CandidateSpec("a", ("a",)),
        CandidateSpec("b", ("b",)),
        CandidateSpec("ab", ("a", "b")),
    )
    result = run({"a": NEUTRAL, "b": NEUTRAL, "ab": NEUTRAL}, specs)
    assert result.decision.status == "UNRESOLVED"


def test_opaque_candidate_names_do_not_change_choice() -> None:
    specs = (
        CandidateSpec("zeta", ("feature_z",)),
        CandidateSpec("alpha", ("feature_a",)),
    )
    first = run({"zeta": MEDIUM, "alpha": GOOD}, specs)
    second = run({"alpha": GOOD, "zeta": MEDIUM}, specs)
    assert first.decision.selected_model_id == "alpha"
    assert second.decision.selected_model_id == "alpha"
