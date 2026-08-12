"""Forensic comparison of similar present states and diverging futures."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tiamat.state_cartography import current_distance, fingerprint


HORIZONS = (1, 3, 6, 12, 24)


@dataclass(frozen=True)
class DivergenceFinding:
    index: int
    current_distance: float
    divergence_horizon: int | None
    divergence_distance: float | None
    status: str


def analyze(
    left: Iterable[float],
    right: Iterable[float],
    *,
    similarity_threshold: float = 0.01,
    divergence_threshold: float = 0.5,
) -> tuple[DivergenceFinding, ...]:
    """Find aligned states that are similar now but separate later.

    The two trajectories are treated as observations only. A non-None
    divergence horizon means the first supported look-ahead at which the
    scalar states exceed the requested separation threshold.
    """
    a = fingerprint(left)
    b = fingerprint(right)
    n = min(len(a), len(b))
    findings: list[DivergenceFinding] = []

    for index in range(n):
        distance_now = current_distance(a[index], b[index])
        if distance_now > similarity_threshold:
            continue

        horizon_found: int | None = None
        divergence_distance: float | None = None
        for horizon in HORIZONS:
            future_index = index + horizon
            if future_index >= n:
                continue
            distance = current_distance(a[future_index], b[future_index])
            if distance > divergence_threshold:
                horizon_found = horizon
                divergence_distance = distance
                break

        status = "divergent" if horizon_found is not None else "consistent"
        findings.append(
            DivergenceFinding(
                index=index,
                current_distance=distance_now,
                divergence_horizon=horizon_found,
                divergence_distance=divergence_distance,
                status=status,
            )
        )

    return tuple(findings)


def summarize(findings: Iterable[DivergenceFinding]) -> dict[str, object]:
    """Return stable aggregate counts and a horizon distribution."""
    items = tuple(findings)
    distribution: dict[int, int] = {}
    for finding in items:
        if finding.divergence_horizon is not None:
            horizon = finding.divergence_horizon
            distribution[horizon] = distribution.get(horizon, 0) + 1

    return {
        "similar_state_pairs": len(items),
        "divergent_futures": sum(f.status == "divergent" for f in items),
        "consistent_futures": sum(f.status == "consistent" for f in items),
        "divergence_horizon_distribution": dict(sorted(distribution.items())),
    }
