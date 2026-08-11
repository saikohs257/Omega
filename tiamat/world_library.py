"""Expanded synthetic-world laboratory and mechanism dictionary.

The dictionary describes capabilities, not expected winners. World generation is
mechanism-driven so the selector must infer which candidates fit the world.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class MechanismProfile:
    name: str
    detects: tuple[str, ...]
    requires: tuple[str, ...] = ()
    weak_against: tuple[str, ...] = ()
    supports_interaction: bool = False


COMPONENT_DICTIONARY: Mapping[str, MechanismProfile] = {
    "state": MechanismProfile("state", ("state", "level")),
    "proximity": MechanismProfile(
        "proximity", ("proximity", "distance_to_boundary"), ("ordered_state",), ("inversion",)
    ),
    "momentum": MechanismProfile(
        "momentum", ("movement", "velocity", "direction"), ("ordered_observations",), ("delay",)
    ),
    "acceleration": MechanismProfile(
        "acceleration", ("movement", "acceleration", "curvature"), ("ordered_observations",)
    ),
    "path": MechanismProfile(
        "path", ("trajectory", "path", "history"), ("ordered_observations",), ("missing_history",)
    ),
    "resistance": MechanismProfile(
        "resistance", ("resistance", "friction", "opposition"), ("ordered_observations",)
    ),
    "delayed": MechanismProfile(
        "delayed", ("lag", "delayed_information", "trajectory"), ("ordered_observations",), ("delay",)
    ),
    "calibrated": MechanismProfile(
        "calibrated", ("probability_scale", "calibration", "confidence")
    ),
    "recovery": MechanismProfile(
        "recovery", ("recovery", "healing", "return_to_baseline"), ("history",)
    ),
    "hysteresis": MechanismProfile(
        "hysteresis", ("history_dependence", "directional_memory"), ("ordered_observations",)
    ),
    "coupling": MechanismProfile(
        "coupling", ("interaction", "joint_relationship", "coupling"), ("multiple_components",), supports_interaction=True
    ),
    "phase": MechanismProfile(
        "phase", ("phase", "alignment", "timing"), ("ordered_observations", "multiple_components")
    ),
}


WORLD_FAMILIES: Mapping[str, tuple[str, ...]] = {
    "state": ("state",),
    "proximity": ("proximity",),
    "movement": ("momentum", "acceleration", "proximity"),
    "trajectory": ("path", "momentum", "acceleration", "delayed"),
    "orientation": ("proximity", "momentum", "phase"),
    "recovery": ("recovery", "state", "path"),
    "resistance": ("resistance", "momentum", "proximity"),
    "hysteresis": ("hysteresis", "path", "momentum"),
    "coupling": ("coupling", "phase", "state"),
    "calibration": ("calibrated", "state"),
}


def select_candidates(mechanisms: set[str]) -> tuple[str, ...]:
    """Return dictionary-compatible candidates without encoding a winner."""
    hits: list[str] = []
    for name, profile in COMPONENT_DICTIONARY.items():
        if set(profile.detects) & mechanisms:
            hits.append(name)
    return tuple(sorted(hits))
