"""V1.1 hand-built TESSERACT_CIRCUIT component reference.

Source provenance:
    TESSERACT_CIRCUIT_V1_1_COMPONENT_FREEZE_20260628

This module implements the frozen, source-backed reference components only.
It is diagnostic/research infrastructure. It does not grant runtime authority.
Learned edge weights remain downstream of strict-table construction and replay.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

EPSILON = 1e-6
OHMS_CAP = 1_000.0
ALPHA = 1.0
BETA = 9.0

RELEASE_PERMISSION = {
    "HOLD_LOCKED": 0.0,
    "RELEASE_PENDING_1_6H": 0.25,
    "RELEASE_OPEN_NOW": 1.0,
    "POST_RELEASE_COOLDOWN": 0.1,
}

LEAKAGE_PATTERNS = (
    "realized_edge",
    "did_edge_happen",
    "actual_next_edge",
    "release_timing_actual",
    "next_move_horizon",
    "next_move_edge",
)


def assert_no_leakage_features(feature_columns: Sequence[str]) -> None:
    bad = [name for name in feature_columns if any(p in name for p in LEAKAGE_PATTERNS)]
    if bad:
        raise ValueError(f"future/target leakage columns used as features: {bad}")


def empirical_conductance(
    edge_release_count: float,
    risk_set_count: float,
    *,
    alpha: float = ALPHA,
    beta: float = BETA,
) -> float:
    """Frozen smoothed release probability over an eligible train risk set."""
    if edge_release_count < 0 or risk_set_count < 0:
        raise ValueError("counts must be non-negative")
    if edge_release_count > risk_set_count:
        raise ValueError("edge_release_count cannot exceed risk_set_count")
    if alpha <= 0 or beta <= 0:
        raise ValueError("alpha and beta must be positive")
    return (edge_release_count + alpha) / (risk_set_count + alpha + beta)


def effective_ohms(conductance: float, *, epsilon: float = EPSILON, cap: float = OHMS_CAP) -> float:
    """Frozen inverse-conductance impedance with a numerical cap."""
    if conductance < 0:
        raise ValueError("conductance must be non-negative")
    if epsilon <= 0 or cap <= 0:
        raise ValueError("epsilon and cap must be positive")
    return min(cap, 1.0 / (epsilon + conductance))


def train_residual(
    train_rows: Sequence[Mapping[str, object]],
    apply_rows: Sequence[Mapping[str, object]],
    *,
    value_key: str,
    group_keys: Sequence[str],
) -> tuple[list[float], list[float]]:
    """Apply a train-only group median residualization rule.

    Missing groups fall back to the train global median. The application set is
    never consulted to estimate expectations.
    """
    if not train_rows:
        raise ValueError("train_rows must not be empty")
    if not group_keys:
        raise ValueError("group_keys must not be empty")

    buckets: dict[tuple[object, ...], list[float]] = {}
    train_values: list[float] = []
    for row in train_rows:
        value = float(row[value_key])
        train_values.append(value)
        key = tuple(row.get(k) for k in group_keys)
        buckets.setdefault(key, []).append(value)

    global_sorted = sorted(train_values)
    mid = len(global_sorted) // 2
    global_median = (
        global_sorted[mid]
        if len(global_sorted) % 2
        else (global_sorted[mid - 1] + global_sorted[mid]) / 2.0
    )

    def median(values: list[float]) -> float:
        s = sorted(values)
        n = len(s)
        m = n // 2
        return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0

    expected = {key: median(values) for key, values in buckets.items()}

    def residual(row: Mapping[str, object]) -> float:
        value = float(row[value_key])
        key = tuple(row.get(k) for k in group_keys)
        return value - expected.get(key, global_median)

    return [residual(r) for r in train_rows], [residual(r) for r in apply_rows]


def release_permission_for(state: str) -> float:
    return RELEASE_PERMISSION.get(str(state), 0.0)


def lit_path_score(
    amp_current_residual: float,
    residual_voltage_to_edge: float,
    conductance: float,
    release_permission: float,
    continuity_prior: float,
    capacitance_lock: float,
    ambiguity_penalty: float = 0.0,
    authority_penalty: float = 0.0,
) -> float:
    """Frozen V1.1 diagnostic score composition.

    This is a reference composition, not a learned weight model and not runtime authority.
    """
    if conductance < 0 or release_permission < 0 or continuity_prior < 0:
        raise ValueError("conductance, release_permission, and continuity_prior must be non-negative")
    denominator = (
        EPSILON
        + max(0.0, capacitance_lock)
        + max(0.0, ambiguity_penalty)
        + max(0.0, authority_penalty)
    )
    numerator = (
        amp_current_residual
        * residual_voltage_to_edge
        * conductance
        * release_permission
        * continuity_prior
    )
    return numerator / denominator
