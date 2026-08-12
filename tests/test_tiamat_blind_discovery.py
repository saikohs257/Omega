"""Blind synthetic discovery tests for TIAMAT candidate selection.

Unlike the 20-world recognition suite, these tests construct raw synthetic
observables first and only then derive candidate predictions.  The selector is
never handed the name of the generating observable; the test oracle retains
that name only for verification after selection.
"""
from __future__ import annotations

from tiamat.model_selection import CandidateSpec
from tiamat.tournament import TournamentCase, TournamentRunner

LABELS = (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1)
FEATURES = (
    "damage", "recovery", "charge", "momentum", "residual_momentum", "residual_load",
    "forcing", "flow", "initial_velocity", "initial_momentum", "initial_trajectory",
    "path", "trajectory", "arc", "route", "track", "orbit", "resistance", "coupling",
)


def _raw_observables(causal: str) -> dict[str, tuple[float, ...]]:
    """Build raw observables without exposing the causal name to the runner."""
    raw: dict[str, tuple[float, ...]] = {}
    for feature in FEATURES:
        if feature == causal:
            # Exactly calibrated .10/.90 signal.  This stays on the canonical
            # ECE boundary without floating-point boundary drift.
            values = tuple(0.90 if y else 0.10 for y in LABELS)
        else:
            values = tuple(0.15 + ((i * 7 + FEATURES.index(feature) * 11) % 70) / 100.0 for i in range(len(LABELS)))
        raw[feature] = values
    return raw


def _prediction_from_observable(values: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(min(0.99, max(0.01, float(v))) for v in values)


def _blind_case(causal: str) -> tuple[TournamentCase, str]:
    raw = _raw_observables(causal)
    order = tuple(reversed(FEATURES))
    specs = tuple(CandidateSpec(f"probe_{name}", (name,), family="blind_probe") for name in order)
    predictions = {f"probe_{name}": _prediction_from_observable(raw[name]) for name in order}
    return (
        TournamentCase(
            name=f"blind_{causal}", labels=LABELS, heldout_predictions=predictions, max_size=1,
        ),
        f"probe_{causal}",
    )


def test_blind_discovery_finds_causal_observable_without_name_hints() -> None:
    for causal in ("damage", "momentum", "path", "trajectory", "coupling"):
        case, expected_model = _blind_case(causal)
        specs = tuple(
            CandidateSpec(model_id=model_id, features=(feature,), family="blind_probe")
            for model_id, feature in zip(
                reversed(tuple(f"probe_{name}" for name in FEATURES)), reversed(FEATURES)
            )
        )
        result = TournamentRunner(specs=specs).run_case(case)
        assert result.decision.status == "SELECTED", causal
        assert result.decision.selected_model_id == expected_model, causal
        assert result.best_model_id == expected_model, causal


def test_blind_discovery_rejects_all_neutral_observables() -> None:
    specs = tuple(CandidateSpec(f"probe_{name}", (name,), family="blind_probe") for name in FEATURES)
    neutral = tuple(0.5 for _ in LABELS)
    result = TournamentRunner(specs=specs).run_case(
        TournamentCase(
            name="blind_unresolved", labels=LABELS,
            heldout_predictions={spec.model_id: neutral for spec in specs}, max_size=1,
        )
    )
    assert result.decision.status == "UNRESOLVED"
    assert result.decision.selected_model_id is None
