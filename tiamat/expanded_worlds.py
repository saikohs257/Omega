"""Expanded deterministic worlds for movement, proximity, inversion and coupling.

These worlds are deliberately generic rather than domain-specific.  Each world
contains labels, observable probability streams, and a mechanism descriptor.
The descriptor is metadata for analysis; it is not used to declare a winner.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ExpandedWorld:
    name: str
    labels: tuple[int, ...]
    predictions: Mapping[str, tuple[float, ...]]
    mechanisms: frozenset[str]
    truth: str | None


def _binary(n: int = 40) -> tuple[int, ...]:
    return tuple(i % 2 for i in range(n))


def _sig(y: tuple[int, ...], low: float = .1, high: float = .9) -> tuple[float, ...]:
    return tuple(high if x else low for x in y)


def _weak(y: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(.55 if x else .45 for x in y)


def _distance(n: int = 40) -> tuple[float, ...]:
    # Oscillating proximity to the 0.5 transition boundary.
    return tuple(abs(((i % 20) / 19.0) - .5) for i in range(n))


def _labels_from_score(score: tuple[float, ...]) -> tuple[int, ...]:
    # Boundary crossing rather than direct use of the score.
    return tuple(int(x < .22) for x in score)


def build_expanded_worlds() -> tuple[ExpandedWorld, ...]:
    y = _binary()
    strong = _sig(y)
    weak = _weak(y)
    worlds: list[ExpandedWorld] = [
        ExpandedWorld("proximity_linear", y, {"proximity": strong, "state": weak}, frozenset({"proximity", "ordered_state"}), "proximity"),
        ExpandedWorld("proximity_nonlinear", y, {"proximity": strong, "calibrated": _sig(y, .02, .98), "state": weak}, frozenset({"proximity", "nonlinear", "ordered_state"}), "proximity"),
        ExpandedWorld("crossing_velocity", y, {"proximity": strong, "momentum": strong, "state": weak}, frozenset({"proximity", "movement", "direction", "ordered_observations"}), "momentum"),
        ExpandedWorld("approach_then_retreat", y, {"proximity": strong, "momentum": _sig(y, .2, .8)}, frozenset({"proximity", "movement", "direction", "history"}), "momentum"),
        ExpandedWorld("near_miss", y, {"proximity": weak, "resistance": strong}, frozenset({"proximity", "resistance", "movement"}), "resistance"),
        ExpandedWorld("constant_velocity", y, {"momentum": strong, "acceleration": weak}, frozenset({"movement", "velocity", "ordered_observations"}), "momentum"),
        ExpandedWorld("accelerating", y, {"acceleration": strong, "momentum": weak}, frozenset({"movement", "acceleration", "ordered_observations"}), "acceleration"),
        ExpandedWorld("decelerating", y, {"resistance": strong, "acceleration": weak}, frozenset({"movement", "deceleration", "resistance", "ordered_observations"}), "resistance"),
        ExpandedWorld("stall_then_release", y, {"path": strong, "momentum": weak}, frozenset({"trajectory", "movement", "history"}), "path"),
        ExpandedWorld("overshoot", y, {"momentum": strong, "hysteresis": strong}, frozenset({"movement", "overshoot", "history_dependence"}), "hysteresis"),
        ExpandedWorld("reversal_after_acceleration", y, {"momentum": weak, "phase": strong}, frozenset({"movement", "direction", "phase", "ordered_observations"}), "phase"),
        ExpandedWorld("phase_reversal", y, {"phase": strong, "state": weak}, frozenset({"phase", "orientation"}), "phase"),
        ExpandedWorld("signed_distance", y, {"proximity": strong, "momentum": weak}, frozenset({"proximity", "orientation", "direction"}), "proximity"),
        ExpandedWorld("mirror_world", y, {"phase": strong, "proximity": weak}, frozenset({"orientation", "phase", "inversion"}), "phase"),
        ExpandedWorld("recovery_curve", y, {"recovery": strong, "state": weak}, frozenset({"recovery", "history"}), "recovery"),
        ExpandedWorld("hysteresis_loop", y, {"hysteresis": strong, "path": weak}, frozenset({"hysteresis", "history_dependence", "directional_memory"}), "hysteresis"),
        ExpandedWorld("coupled_threshold", y, {"A": weak, "B": weak, "coupling": strong}, frozenset({"coupling", "interaction", "multiple_components"}), "coupling"),
        ExpandedWorld("phase_coupling", y, {"A": weak, "B": weak, "coupling": strong, "phase": strong}, frozenset({"coupling", "phase", "multiple_components"}), "coupling"),
        ExpandedWorld("redundant_state_damage", y, {"state": strong, "damage": strong, "noise": weak}, frozenset({"redundancy", "state"}), "state_or_damage"),
        ExpandedWorld("unknown_world", y, {"A": (.5,) * len(y), "B": (.5,) * len(y)}, frozenset({"unknown"}), None),
    ]
    # A deliberately label-independent proximity family for additional scale.
    d = _distance()
    yd = _labels_from_score(d)
    worlds.extend([
        ExpandedWorld("proximity_boundary", yd, {"proximity": tuple(1.0 - x for x in d), "state": (.5,) * len(yd)}, frozenset({"proximity", "ordered_state"}), "proximity"),
        ExpandedWorld("proximity_with_resistance", yd, {"proximity": tuple(1.0 - x for x in d), "resistance": tuple(.9 if x < .22 else .1 for x in d)}, frozenset({"proximity", "resistance", "movement"}), "resistance"),
    ])
    return tuple(worlds)
