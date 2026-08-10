"""Broad TIAMAT candidate observable library.

These names are hypotheses/observables, not canonical state variables. The
model-selection layer decides whether combinations earn authority.
"""
from __future__ import annotations

from .model_selection import CandidateSpec

CANDIDATE_FEATURES: tuple[str, ...] = (
    # Core latent/state candidates.
    "damage", "recovery", "charge", "momentum", "residual_momentum",
    "residual_load", "baseline", "forcing", "capacity", "headroom",
    # Motion / derivatives.
    "velocity", "initial_velocity", "initial_momentum", "acceleration", "jerk",
    "flow", "phase_velocity", "phase_acceleration", "signed_impulse",
    # Path / geometry.
    "position", "initial_position", "displacement", "path", "initial_trajectory",
    "trajectory", "arc", "curvature", "turning_rate", "route", "track",
    "orbit", "orbit_period", "orbit_drift", "path_efficiency", "return_distance",
    "basin_distance", "separatrix_distance",
    # History / hysteresis.
    "episode_age", "mode_age", "dwell_time", "reversal_count", "return_point_memory",
    "hysteresis_memory", "arrival_context", "arrival_velocity", "arrival_acceleration",
    # Load / circuit analogues.
    "residual_charge", "resistance", "conductance", "tension", "pressure",
    "energy", "stiffness", "transfer_pressure", "coupling", "connectivity",
    # Existing structural/trajectory descriptors.
    "tightness", "trajectory_class", "run_age", "pulse_acceleration", "baseline_elevation",
    "asymmetric_drift",
)

CANDIDATE_FAMILIES: dict[str, tuple[str, ...]] = {
    "core": ("damage", "charge", "momentum", "recovery"),
    "loading": ("forcing", "baseline", "pressure", "tension", "residual_load"),
    "motion": ("velocity", "momentum", "acceleration", "jerk", "flow"),
    "initial": ("initial_position", "initial_velocity", "initial_momentum", "initial_trajectory"),
    "path": ("path", "trajectory", "displacement", "arc", "curvature", "path_efficiency"),
    "route": ("route", "track", "orbit", "orbit_period", "orbit_drift"),
    "history": ("episode_age", "mode_age", "dwell_time", "reversal_count", "hysteresis_memory", "arrival_context"),
    "capacity": ("capacity", "headroom", "resistance", "conductance", "recovery"),
    "topology": ("coupling", "connectivity", "transfer_pressure"),
}

DEFAULT_CANDIDATE_MODELS: tuple[CandidateSpec, ...] = (
    CandidateSpec("M_D", ("damage",), family="core"),
    CandidateSpec("M_DV", ("damage", "momentum"), family="core"),
    CandidateSpec("M_DQV", ("damage", "charge", "momentum"), family="core"),
    CandidateSpec("M_DQRV", ("damage", "charge", "recovery", "momentum"), family="core"),
    CandidateSpec("M_DQVF", ("damage", "charge", "momentum", "forcing"), family="loading"),
    CandidateSpec("M_DQVPATH", ("damage", "charge", "momentum", "trajectory"), family="path"),
    CandidateSpec("M_DQVCPL", ("damage", "charge", "momentum", "coupling"), family="topology"),
    CandidateSpec("M_FULL_CONTEXT", CANDIDATE_FEATURES, family="full"),
)
