from __future__ import annotations

from dataclasses import dataclass, asdict
from statistics import mean
from typing import Sequence

from tiamat.state_cartography import fingerprint, current_distance

HORIZONS = (1, 3, 6, 12, 24)


@dataclass(frozen=True)
class PairFinding:
    left: int
    right: int
    current_distance: float
    future_distances: tuple[float, ...]
    divergence_horizon: int | None


def future_distance(values_a: Sequence[float], values_b: Sequence[float], start: int, horizon: int) -> float:
    end = min(start + horizon + 1, len(values_a), len(values_b))
    if end <= start + 1:
        return 0.0
    return mean(abs(float(a) - float(b)) for a, b in zip(values_a[start + 1:end], values_b[start + 1:end]))


def first_divergence(distances: Sequence[float], horizons: Sequence[int] = HORIZONS, threshold: float = 0.5) -> int | None:
    for horizon, distance in zip(horizons, distances):
        if distance >= threshold:
            return horizon
    return None


def find_similar_pairs(values_a: Sequence[float], values_b: Sequence[float], threshold: float = 0.2):
    fa = fingerprint(values_a)
    fb = fingerprint(values_b)
    for i, a in enumerate(fa):
        for j, b in enumerate(fb):
            d = current_distance(a, b)
            if d <= threshold:
                yield i, j, d


def analyze_pair(values_a: Sequence[float], values_b: Sequence[float], left: int, right: int, current_d: float, threshold: float = 0.5) -> PairFinding:
    distances = tuple(future_distance(values_a, values_b, left, h) for h in HORIZONS)
    return PairFinding(left, right, current_d, distances, first_divergence(distances, threshold=threshold))


def analyze(values_a: Sequence[float], values_b: Sequence[float], *, similarity_threshold: float = 0.2, divergence_threshold: float = 0.5) -> list[PairFinding]:
    return [analyze_pair(values_a, values_b, i, j, d, divergence_threshold) for i, j, d in find_similar_pairs(values_a, values_b, similarity_threshold)]


def summarize(findings: Sequence[PairFinding]) -> dict:
    divergent = [f for f in findings if f.divergence_horizon is not None]
    consistent = [f for f in findings if f.divergence_horizon is None]
    horizons = [f.divergence_horizon for f in divergent]
    return {
        "similar_state_pairs": len(findings),
        "consistent_futures": len(consistent),
        "divergent_futures": len(divergent),
        "divergence_horizon_distribution": {str(h): horizons.count(h) for h in HORIZONS if h in horizons},
        "mean_current_distance": mean(f.current_distance for f in findings) if findings else 0.0,
    }


if __name__ == "__main__":
    # Small deterministic smoke experiment. Real-world adapters should feed
    # observation windows into analyze(); no future-derived fields are used.
    a = [0.0] * 8 + [0.0, 0.0, 0.0, 0.0]
    b = [0.0] * 8 + [0.0, 0.0, 1.0, 1.0]
    findings = analyze(a, b, similarity_threshold=0.01, divergence_threshold=0.5)
    print(summarize(findings))
