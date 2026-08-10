"""Deterministic synthetic worlds for adversarial TIAMAT discovery tests.

These worlds deliberately encode different causal geometries without teaching the
selector which observable is supposed to win.  They provide labels plus named
held-out probability streams so the tournament can be tested independently of
any particular model-fitting implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class AdversarialWorld:
    """A small held-out world with an explicit generating mechanism label."""

    name: str
    labels: tuple[int, ...]
    predictions: Mapping[str, tuple[float, ...]]
    truth_mechanism: str


def _labels(n: int = 20) -> tuple[int, ...]:
    return tuple(i % 2 for i in range(n))


def _signal(labels: tuple[int, ...], low: float = 0.10, high: float = 0.90) -> tuple[float, ...]:
    return tuple(high if y else low for y in labels)


def _weak_rank(labels: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(0.51 if y else 0.49 for y in labels)


def _inverse(labels: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(0.90 if not y else 0.10 for y in labels)


def build_adversarial_worlds() -> tuple[AdversarialWorld, ...]:
    """Return deterministic worlds covering distinct failure modes."""
    y = _labels()
    neutral = (0.50,) * len(y)
    strong = _signal(y)
    weak = _weak_rank(y)
    inverse = _inverse(y)

    # The first half carries one mechanism and the second half another.  A
    # globally conflicting candidate should not be promoted merely for local fit.
    regime_conflict = tuple(
        0.90 if label else 0.10
        if i < len(y) // 2
        else 0.10 if label else 0.90
        for i, label in enumerate(y)
    )

    # Interaction-only: neither component has information by itself, while the
    # supplied joint hypothesis does.
    interaction = tuple(0.90 if label else 0.10 for label in y)

    # Delayed signal: instantaneous proxy is weak; delayed proxy is strong.
    return (
        AdversarialWorld("clean_state", y, {"state": strong, "noise": neutral}, "state"),
        AdversarialWorld("auc_trap", y, {"state": weak, "noise": neutral}, "none"),
        AdversarialWorld("inverse_signal", y, {"state": inverse, "noise": neutral}, "none"),
        AdversarialWorld("calibration_deception", y, {"overranked": weak, "calibrated": strong}, "calibrated"),
        AdversarialWorld("interaction_only", y, {"A": neutral, "B": neutral, "A_x_B": interaction}, "A_x_B"),
        AdversarialWorld("delayed_trajectory", y, {"instant": weak, "delayed": strong}, "delayed"),
        AdversarialWorld("regime_conflict", y, {"global": regime_conflict, "neutral": neutral}, "none"),
        AdversarialWorld("no_signal", y, {"A": neutral, "B": neutral, "C": neutral}, "none"),
        AdversarialWorld("redundant_signal", y, {"state": strong, "damage": strong, "noise": neutral}, "state_or_damage"),
        AdversarialWorld("path_signal", y, {"path": strong, "instant": weak}, "path"),
        AdversarialWorld("momentum_signal", y, {"initial_momentum": strong, "residual": weak}, "initial_momentum"),
        AdversarialWorld("resistance_signal", y, {"resistance": strong, "flow": weak}, "resistance"),
    )
