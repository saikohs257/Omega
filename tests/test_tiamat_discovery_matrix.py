"""Adversarial blind discovery matrix for the TIAMAT tournament.

These worlds deliberately vary the mechanism presented to the selector:
state, momentum, trajectory/path, delayed evidence, interaction-only evidence,
redundant proxies, regime disagreement, and no-signal. The runner receives only
opaque candidate IDs and held-out probabilities; the generating mechanism is
retained only by the test oracle.
"""
from __future__ import annotations

from tiamat.model_selection import CandidateSpec, ModelSelector
from tiamat.tournament import TournamentCase, TournamentRunner

LABELS = (0, 1) * 12
GOOD = tuple(0.08 if y == 0 else 0.92 for y in LABELS)
NEUTRAL = tuple(0.50 for _ in LABELS)
NOISY = tuple(0.22 if y == 0 else 0.78 for y in LABELS)


def _specs(*names: str) -> tuple[CandidateSpec, ...]:
    return tuple(CandidateSpec(f"probe_{name}", (name,), family="blind_matrix") for name in names)


def _run(candidates: dict[str, tuple[float, ...]], *, selector: ModelSelector | None = None, max_size: int = 1):
    specs = _specs(*tuple(reversed(candidates)))
    return TournamentRunner(selector=selector or ModelSelector(), specs=specs).run_case(
        TournamentCase(
            name="matrix",
            labels=LABELS,
            heldout_predictions={f"probe_{k}": v for k, v in candidates.items()},
            max_size=max_size,
        )
    )


def test_matrix_finds_state_signal_against_redundant_proxies() -> None:
    result = _run({"state": GOOD, "proxy_a": NOISY, "proxy_b": NOISY, "neutral": NEUTRAL})
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "probe_state"


def test_matrix_finds_delayed_signal_over_instantaneous_proxy() -> None:
    result = _run({"instantaneous": NOISY, "delayed_trajectory": GOOD, "neutral": NEUTRAL})
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "probe_delayed_trajectory"


def test_matrix_finds_path_when_state_is_neutral() -> None:
    result = _run({"state": NEUTRAL, "path": GOOD, "momentum": NOISY})
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "probe_path"


def test_matrix_rejects_high_auc_poor_calibration_candidate() -> None:
    selector = ModelSelector(max_calibration_error=0.10, min_brier_skill=0.05)
    misleading = tuple(0.49 if y == 0 else 0.99 for y in LABELS)
    result = _run({"good": GOOD, "overconfident": misleading, "neutral": NEUTRAL}, selector=selector)
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "probe_good"
    assert "probe_overconfident" not in result.decision.candidates


def test_matrix_interaction_candidate_beats_neutral_singletons() -> None:
    interaction = GOOD
    specs = (
        CandidateSpec("probe_a", ("a",)),
        CandidateSpec("probe_b", ("b",)),
        CandidateSpec("probe_a_b", ("a", "b")),
    )
    result = TournamentRunner(specs=specs).run_case(
        TournamentCase(
            name="interaction_only",
            labels=LABELS,
            heldout_predictions={
                "probe_a": NEUTRAL,
                "probe_b": NEUTRAL,
                "probe_a_b": interaction,
            },
            max_size=2,
        )
    )
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "probe_a_b"


def test_matrix_regime_disagreement_can_remain_unresolved() -> None:
    left = tuple(0.08 if y == 0 else 0.92 for y in LABELS[:12])
    right = tuple(0.92 if y == 0 else 0.08 for y in LABELS[12:])
    contested = left + right
    result = _run({"regime_conflict": contested, "neutral": NEUTRAL})
    assert result.decision.status == "UNRESOLVED"
    assert result.decision.selected_model_id is None


def test_matrix_no_signal_is_unresolved() -> None:
    result = _run({"path": NEUTRAL, "trajectory": NEUTRAL, "orbit": NEUTRAL})
    assert result.decision.status == "UNRESOLVED"
    assert result.decision.selected_model_id is None
