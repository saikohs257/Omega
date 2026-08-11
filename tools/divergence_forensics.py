from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence, Any

from tiamat.state_cartography import current_distance, fingerprint


HORIZONS = (1, 3, 6, 12, 24)


@dataclass(frozen=True)
class DivergenceFinding:
    """One pair of similar present states whose futures separate."""

    index: int
    current_distance: float
    divergence_horizon: int | None
    future_distance: float | None


def analyze(
    a: Sequence[Any],
    b: Sequence[Any],
    *,
    similarity_threshold: float = 0.01,
    divergence_threshold: float = 0.5,
) -> tuple[DivergenceFinding, ...]:
    """Find present-state matches followed by measurable future divergence.

    Similarity is evaluated only at the present index.  Future samples are
    consulted only after a pair has passed that current-state gate, preventing
    future information from contaminating the state fingerprint.
    """
    if len(a) != len(b):
        raise ValueError("trajectories must have equal length")
    if not a:
        return ()

    af = fingerprint(a)
    bf = fingerprint(b)
    findings: list[DivergenceFinding] = []

    for index in range(len(a)):
        present = current_distance(af[index], bf[index])
        if present > similarity_threshold:
            continue

        horizon = None
        future_distance = None
        for h in HORIZONS:
            target = index + h
            if target >= len(a):
                continue
            distance = current_distance(af[target], bf[target])
            if distance > divergence_threshold:
                horizon = h
                future_distance = distance
                break

        if horizon is not None:
            findings.append(
                DivergenceFinding(index, present, horizon, future_distance)
            )

    return tuple(findings)


def summarize(findings: Sequence[DivergenceFinding]) -> dict[str, Any]:
    """Summarize divergence findings for machine-readable reporting."""
    divergent = [f for f in findings if f.divergence_horizon is not None]
    horizons = Counter(f.divergence_horizon for f in divergent)
    return {
        "similar_state_pairs": len(findings),
        "divergent_futures": len(divergent),
        "consistent_futures": len(findings) - len(divergent),
        "divergence_horizon_distribution": {
            str(h): horizons[h] for h in sorted(horizons)
        },
    }
