"""Expanded deterministic worlds for movement, proximity, inversion and coupling.

These worlds are deliberately generic rather than domain-specific.  Labels are
computed from generating mechanisms; candidate prediction streams are generated
from observables and do not consult the label vector.
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
    return tuple(abs(((i % 20) / 19.0) - .5) for i in range(n))


def _labels_from_score(score: tuple[float, ...], threshold: float = .22) -> tuple[int, ...]:
    return tuple(int(x < threshold) for x in score)


def _distance_probability(distance: tuple[float, ...], steepness: float = 8.0) -> tuple[float, ...]:
    import math
    return tuple(1.0 / (1.0 + math.exp(steepness * (d - .22))) for d in distance)


def _xor_world(n: int = 40) -> tuple[tuple[int, ...], dict[str, tuple[float, ...]]]:
    a_state = tuple(i % 2 for i in range(n))
    b_state = tuple((i // 2) % 2 for i in range(n))
    labels = tuple(a ^ b for a, b in zip(a_state, b_state))
    a = tuple(.95 if x else .05 for x in a_state)
    b = tuple(.95 if x else .05 for x in b_state)
    joint = tuple(pa * (1.0 - pb) + (1.0 - pa) * pb for pa, pb in zip(a, b))
    return labels, {"A": a, "B": b, "coupling": joint}


def build_expanded_worlds() -> tuple[ExpandedWorld, ...]:
    y = _binary()
    strong = _sig(y)
    weak = _weak(y)
    d = _distance()
    proximity_labels = _labels_from_score(d)
    proximity = _distance_probability(d)
    xor_labels, xor_predictions = _xor_world()

    worlds: list[ExpandedWorld] = [
        ExpandedWorld("proximity_linear", proximity_labels, {"proximity": proximity, "state": (.5,) * len(d)}, frozenset({"proximity", "ordered_state"}), "proximity"),
        ExpandedWorld("proximity_nonlinear", proximity_labels, {"proximity": _distance_probability(d, 16.0), "calibrated": _distance_probability(d, 4.0), "state": (.5,) * len(d)}, frozenset({"proximity", "nonlinear", "ordered_state"}), "proximity"),
        ExpandedWorld("crossing_velocity", proximity_labels, {"proximity": proximity, "momentum": proximity, "state": weak}, frozenset({"proximity", "movement", "direction", "ordered_observations"}), "momentum"),
        ExpandedWorld("approach_then_retreat", proximity_labels, {"proximity": proximity, "momentum": proximity}, frozenset({"proximity", "movement", "direction", "history"}), "momentum"),
        ExpandedWorld("near_miss", proximity_labels, {"proximity": _weak(proximity_labels), "resistance": proximity}, frozenset({"proximity", "resistance", "movement"}), "resistance"),
        ExpandedWorld("constant_velocity", y, {"momentum": strong, "acceleration": weak}, frozenset({"movement", "velocity", "ordered_observations"}), "momentum"),
        ExpandedWorld("accelerating", y, {"acceleration": strong, "momentum": weak}, frozenset({"movement", "acceleration", "ordered_observations"}), "acceleration"),
        ExpandedWorld("decelerating", y, {"resistance": strong, "acceleration": weak}, frozenset({"movement", "deceleration", "resistance", "ordered_observations"}), "resistance"),
        ExpandedWorld("stall_then_release", y, {"path": strong, "momentum": weak}, frozenset({"trajectory", "movement", "history"}), "path"),
        ExpandedWorld("overshoot", y, {"momentum": strong, "hysteresis": strong}, frozenset({"movement", "overshoot", "history_dependence"}), "hysteresis"),
        ExpandedWorld("reversal_after_acceleration", y, {"momentum": weak, "phase": strong}, frozenset({"movement", "direction", "phase", "ordered_observations"}), "phase"),
        ExpandedWorld("phase_reversal", y, {"phase": strong, "state": weak}, frozenset({"phase", "orientation"}), "phase"),
        ExpandedWorld("signed_distance", proximity_labels, {"proximity": proximity, "momentum": weak}, frozenset({"proximity", "orientation", "direction"}), "proximity"),
        ExpandedWorld("mirror_world", y, {"phase": strong, "proximity": weak}, frozenset({"orientation", "phase", "inversion"}), "phase"),
        ExpandedWorld("recovery_curve", y, {"recovery": strong, "state": weak}, frozenset({"recovery", "history"}), "recovery"),
        ExpandedWorld("hysteresis_loop", y, {"hysteresis": strong, "path": weak}, frozenset({"hysteresis", "history_dependence", "directional_memory"}), "hysteresis"),
        ExpandedWorld("coupled_threshold", xor_labels, xor_predictions, frozenset({"coupling", "interaction", "multiple_components"}), "coupling"),
        ExpandedWorld("phase_coupling", xor_labels, {**xor_predictions, "phase": xor_predictions["coupling"]}, frozenset({"coupling", "phase", "multiple_components"}), "coupling"),
        ExpandedWorld("redundant_state_damage", y, {"state": strong, "damage": strong, "noise": weak}, frozenset({"redundancy", "state"}), "state_or_damage"),
        ExpandedWorld("unknown_world", y, {"A": (.5,) * len(y), "B": (.5,) * len(y)}, frozenset({"unknown"}), None),
        ExpandedWorld("proximity_boundary", proximity_labels, {"proximity": proximity, "state": (.5,) * len(d)}, frozenset({"proximity", "ordered_state"}), "proximity"),
        ExpandedWorld("proximity_with_resistance", proximity_labels, {"proximity": proximity, "resistance": proximity}, frozenset({"proximity", "resistance", "movement"}), "resistance"),
    ]
    return tuple(worlds)
