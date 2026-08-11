"""Causal forensic analysis for trajectory-first state representations.

This module deliberately does not cluster, classify, or promote mechanisms. It
finds present-state pairs that look similar, compares their *observed* futures,
and reports where futures first diverge. Candidate explanatory dimensions can
then be supplied separately from information available at or before that time.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Mapping, Sequence

from tiamat.state_cartography import StateFingerprint, current_distance, fingerprint

HORIZONS = (1, 3, 6, 12, 24)


@dataclass(frozen=True, slots=True)
class SimilarPair:
    left: int
    right: int
    current_distance: float


@dataclass(frozen=True, slots=True)
class PairFinding:
    left: int
    right: int
    current_distance: float
    future_distances: tuple[float, ...]
    divergence_horizon: int | None


def future_distance(
    fingerprints_a: Sequence[StateFingerprint],
    fingerprints_b: Sequence[StateFingerprint],
    start: int,
    horizon: int,
) -> float:
    """Compare only future observed values; derived state is never compared."""
    if start < 0 or start >= len(fingerprints_a) or start >= len(fingerprints_b):
        raise ValueError("start must fall inside both trajectories")
    end = min(start + horizon + 1, len(fingerprints_a), len(fingerprints_b))
    if end <= start + 1:
        return 0.0
    values = [
        abs(a.value - b.value)
        for a, b in zip(fingerprints_a[start + 1:end], fingerprints_b[start + 1:end])
    ]
    return mean(values)


def find_similar_states(
    values_a: Sequence[float],
    values_b: Sequence[float],
    *,
    similarity_threshold: float = 0.2,
    exclude_same_time: bool = False,
) -> tuple[SimilarPair, ...]:
    """Find instantaneous state pairs close under value/velocity/acceleration."""
    fa = fingerprint(values_a)
    fb = fingerprint(values_b)
    pairs: list[SimilarPair] = []
    for i, a in enumerate(fa):
        for j, b in enumerate(fb):
            if exclude_same_time and i == j:
                continue
            distance = current_distance(a, b)
            if distance <= similarity_threshold:
                pairs.append(SimilarPair(i, j, distance))
    return tuple(pairs)


def first_divergence(
    distances: Sequence[float],
    *,
    horizons: Sequence[int] = HORIZONS,
    threshold: float = 0.5,
) -> int | None:
    """Return the earliest fixed horizon crossing the divergence threshold."""
    for horizon, distance in zip(horizons, distances):
        if distance >= threshold:
            return horizon
    return None


def analyze_pair(
    values_a: Sequence[float],
    values_b: Sequence[float],
    pair: SimilarPair,
    *,
    horizons: Sequence[int] = HORIZONS,
    divergence_threshold: float = 0.5,
) -> PairFinding:
    fa = fingerprint(values_a)
    fb = fingerprint(values_b)
    distances = tuple(future_distance(fa, fb, pair.left, h) for h in horizons)
    return PairFinding(
        pair.left,
        pair.right,
        pair.current_distance,
        distances,
        first_divergence(distances, horizons=horizons, threshold=divergence_threshold),
    )


def analyze(
    values_a: Sequence[float],
    values_b: Sequence[float],
    *,
    similarity_threshold: float = 0.2,
    divergence_threshold: float = 0.5,
    horizons: Sequence[int] = HORIZONS,
) -> tuple[PairFinding, ...]:
    """Run the complete similar-now/future-divergence forensic pass."""
    pairs = find_similar_states(
        values_a, values_b, similarity_threshold=similarity_threshold
    )
    return tuple(
        analyze_pair(
            values_a,
            values_b,
            pair,
            horizons=horizons,
            divergence_threshold=divergence_threshold,
        )
        for pair in pairs
        if pair.left + max(horizons) < len(values_a)
        and pair.left + max(horizons) < len(values_b)
    )


def candidate_pre_divergence_differences(
    dimensions_a: Mapping[str, Sequence[float]],
    dimensions_b: Mapping[str, Sequence[float]],
    *,
    left: int,
    right: int,
) -> tuple[tuple[str, float], ...]:
    """Rank differences using values available at the compared current time.

    This is deliberately descriptive: it does not claim causality or promote a
    dimension. Callers should aggregate recurrence across independent episodes.
    """
    common = sorted(set(dimensions_a).intersection(dimensions_b))
    ranked = []
    for name in common:
        a = dimensions_a[name]
        b = dimensions_b[name]
        if left >= len(a) or right >= len(b):
            continue
        ranked.append((name, abs(float(a[left]) - float(b[right]))))
    ranked.sort(key=lambda item: item[1], reverse=True)
    return tuple(ranked)


def summarize(findings: Sequence[PairFinding]) -> dict:
    divergent = [f for f in findings if f.divergence_horizon is not None]
    horizons = [f.divergence_horizon for f in divergent]
    return {
        "similar_state_pairs": len(findings),
        "consistent_futures": len(findings) - len(divergent),
        "divergent_futures": len(divergent),
        "divergence_horizon_distribution": {
            str(h): horizons.count(h) for h in HORIZONS if h in horizons
        },
        "mean_current_distance": mean(f.current_distance for f in findings) if findings else 0.0,
        "findings": [asdict(f) for f in findings],
    }
