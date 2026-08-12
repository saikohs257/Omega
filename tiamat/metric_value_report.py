"""Controlled metric-disagreement experiment for TIAMAT.

This is a research instrument, not a tournament selector. It constructs small,
known cases where AUC, Brier, and LogLoss answer different questions and
reports the metric profiles without naming a universal winner.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .metric_discovery import TargetKind, binary_metric_profile, hidden_state_metric_profile


@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    target: TargetKind
    probabilities: tuple[float, ...] | None = None
    labels: tuple[int, ...] | None = None
    multiclass_probabilities: tuple[tuple[float, ...], ...] | None = None
    interpretation: str = ""


def controlled_scenarios() -> tuple[Scenario, ...]:
    """Return scenarios designed to separate metric meanings."""
    labels = (0, 0, 1, 1)
    return (
        Scenario(
            "perfect_rank_but_poor_calibration",
            TargetKind.EVENT,
            probabilities=(0.41, 0.49, 0.51, 0.59),
            labels=labels,
            interpretation="AUC can be perfect while probability quality remains modest.",
        ),
        Scenario(
            "perfectly_calibrated_binary",
            TargetKind.EVENT,
            probabilities=(0.0, 0.0, 1.0, 1.0),
            labels=labels,
            interpretation="A clean event case where ranking and probability quality agree.",
        ),
        Scenario(
            "hidden_state_uncertainty",
            TargetKind.HIDDEN_STATE,
            multiclass_probabilities=(
                (0.70, 0.20, 0.10),
                (0.20, 0.60, 0.20),
                (0.10, 0.20, 0.70),
                (0.34, 0.33, 0.33),
            ),
            labels=(0, 1, 2, 0),
            interpretation="A latent-state belief distribution contains information that top-1 accuracy compresses away.",
        ),
        Scenario(
            "hidden_state_overconfidence",
            TargetKind.HIDDEN_STATE,
            multiclass_probabilities=(
                (0.99, 0.005, 0.005),
                (0.005, 0.99, 0.005),
                (0.005, 0.005, 0.99),
                (0.90, 0.05, 0.05),
            ),
            labels=(0, 1, 2, 1),
            interpretation="Top-1 can look strong while LogLoss/Brier expose confident wrong beliefs.",
        ),
    )


def evaluate_scenario(scenario: Scenario) -> dict[str, float]:
    """Score a controlled scenario using every metric applicable to its target."""
    if scenario.target == TargetKind.HIDDEN_STATE:
        assert scenario.multiclass_probabilities is not None
        assert scenario.labels is not None
        profile = hidden_state_metric_profile(scenario.multiclass_probabilities, scenario.labels)
    else:
        assert scenario.probabilities is not None
        assert scenario.labels is not None
        profile = binary_metric_profile(scenario.probabilities, scenario.labels, target=scenario.target)
    return {item.name: item.value for item in profile.observations}


def metric_disagreement_matrix() -> dict[str, dict[str, float]]:
    """Return metric values by scenario without applying a primary-metric rule."""
    return {scenario.name: evaluate_scenario(scenario) for scenario in controlled_scenarios()}


def format_report() -> str:
    """Render a deterministic text report suitable for CI logs."""
    lines = ["TIAMAT CONTROLLED METRIC DISAGREEMENT REPORT"]
    for scenario in controlled_scenarios():
        values = evaluate_scenario(scenario)
        ordered = ", ".join(f"{name}={value:.6f}" for name, value in sorted(values.items()))
        lines.append(f"SCENARIO {scenario.name} | target={scenario.target.value} | {ordered}")
        lines.append(f"  {scenario.interpretation}")
    lines.append("NO_PRIMARY_METRIC=TRUE")
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report())
