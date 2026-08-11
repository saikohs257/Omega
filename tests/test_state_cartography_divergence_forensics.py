from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from tiamat.state_cartography import StateFingerprint, current_distance, fingerprint


@dataclass(frozen=True)
class DivergenceCase:
    left: int
    right: int
    current_distance: float
    horizon: int
    future_distance: float


def _future_distance(values_a, values_b, start, horizon):
    end = min(start + horizon + 1, len(values_a), len(values_b))
    if end <= start + 1:
        return 0.0
    return mean(abs(a - b) for a, b in zip(values_a[start + 1:end], values_b[start + 1:end]))


def _first_divergence(values_a, values_b, start, horizons=(1, 3, 6, 12, 24), threshold=0.5):
    for h in horizons:
        d = _future_distance(values_a, values_b, start, h)
        if d >= threshold:
            return h, d
    return None


def _similar_pairs(values_a, values_b, max_current_distance=0.2):
    fa = fingerprint(values_a)
    fb = fingerprint(values_b)
    out = []
    for i in range(len(fa)):
        for j in range(len(fb)):
            d = current_distance(fa[i], fb[j])
            if d <= max_current_distance:
                out.append((i, j, d))
    return out


def test_future_consistency_and_divergence_forensics_detect_divergence():
    # Same present state, but one trajectory contains a latent pre-existing
    # offset that becomes observable only after the current point.
    left = [0.0] * 8 + [0.0, 0.0, 0.0, 0.0]
    right = [0.0] * 8 + [0.0, 0.0, 1.0, 1.0]
    pairs = _similar_pairs(left, right, max_current_distance=0.01)
    assert pairs
    result = _first_divergence(left, right, 7, horizons=(1, 3, 6))
    assert result is not None
    assert result[0] == 3


def test_future_distance_uses_observations_not_derived_state():
    # Different historical derivative paths converge to the same observed
    # future.  Future consistency must therefore remain near zero.
    left = [0, 1, 2, 3, 3, 3, 3, 3]
    right = [3, 2, 1, 0, 3, 3, 3, 3]
    fa = fingerprint(left)
    fb = fingerprint(right)
    assert abs(_future_distance(left, right, 4, 3)) < 1e-12
    assert abs(fa[4].value - fb[4].value) < 1e-12


def test_divergence_forensics_reports_fixed_horizons():
    left = [float(x) for x in range(20)]
    right = [float(x) for x in range(20)]
    right[10:] = [x + 2.0 for x in right[10:]]
    horizons = (1, 3, 6, 12, 24)
    measurements = [_future_distance(left, right, 8, h) for h in horizons]
    assert len(measurements) == 5
    assert measurements[0] < measurements[-1]
