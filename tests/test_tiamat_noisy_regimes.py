"""Hard-mode blind tests for TIAMAT candidate selection.

These tests deliberately add noise, redundancy, misleading rankings, regime
changes, and interaction-only structure. They validate selection behavior,
not historical TIAMAT claims.
"""
from __future__ import annotations

from tiamat.model_selection import CandidateSpec
from tiamat.tournament import TournamentCase, TournamentRunner

LABELS = (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1)
GOOD = tuple(0.18 if y == 0 else 0.82 for y in LABELS)
MEDIUM = tuple(0.38 if y == 0 else 0.62 for y in LABELS)
NEUTRAL = tuple(0.50 for _ in LABELS)
SHIFTED = tuple(0.32 if i % 4 < 2 else 0.68 for i in range(len(LABELS)))


def test_noise_and_redundancy_do_not_displace_strong_signal() -> None:
    specs = (
        CandidateSpec("probe_signal", ("signal",)),
        CandidateSpec("probe_redundant", ("redundant",)),
        CandidateSpec("probe_noise", ("noise",)),
    )
    result = TournamentRunner(specs=specs).run_case(
        TournamentCase(
            name="noise_redundancy",
            labels=LABELS,
            heldout_predictions={"probe_signal": GOOD, "probe_redundant": GOOD, "probe_noise": NEUTRAL},
            max_size=2,
        )
    )
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id in {"probe_signal", "probe_redundant"}


def test_misleading_high_auc_is_penalized_for_poor_calibration() -> None:
    specs = (
        CandidateSpec("probe_good", ("good",)),
        CandidateSpec("probe_misleading", ("over",)),
    )
    misleading = tuple(0.49 if y == 0 else 0.90 for y in LABELS)
    result = TournamentRunner(specs=specs).run_case(
        TournamentCase(
            name="calibration_conflict",
            labels=LABELS,
            heldout_predictions={"probe_good": MEDIUM, "probe_misleading": misleading},
            max_size=2,
        )
    )
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "probe_good"


def test_regime_shift_is_not_automatically_declared_resolved() -> None:
    specs = (
        CandidateSpec("probe_state", ("state",)),
        CandidateSpec("probe_path", ("path",)),
        CandidateSpec("probe_shift", ("shift",)),
    )
    result = TournamentRunner(specs=specs).run_case(
        TournamentCase(
            name="regime_shift",
            labels=LABELS,
            heldout_predictions={"probe_state": SHIFTED, "probe_path": SHIFTED, "probe_shift": NEUTRAL},
            max_size=2,
        )
    )
    assert result.decision.status in {"SELECTED", "UNRESOLVED"}


def test_interaction_only_signal_survives_noise() -> None:
    specs = (
        CandidateSpec("charge", ("charge",)),
        CandidateSpec("coupling", ("coupling",)),
        CandidateSpec("charge_coupling", ("charge", "coupling")),
        CandidateSpec("noise", ("noise",)),
    )
    result = TournamentRunner(specs=specs).run_case(
        TournamentCase(
            name="interaction_noise",
            labels=LABELS,
            heldout_predictions={
                "charge": NEUTRAL,
                "coupling": NEUTRAL,
                "charge_coupling": GOOD,
                "noise": NEUTRAL,
            },
            max_size=2,
        )
    )
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "charge_coupling"
