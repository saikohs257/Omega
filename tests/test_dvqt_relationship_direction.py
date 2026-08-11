import numpy as np

from tools.relationship_map import _directional_gap


def test_directional_gap_detects_temporal_ordering():
    rng = np.random.default_rng(7)
    a = rng.normal(size=300)
    b = np.empty_like(a)
    b[0] = rng.normal()
    b[1:] = a[:-1] + 0.05 * rng.normal(size=299)
    y = (b > np.median(b)).astype(int)
    gap = _directional_gap(a, b, "multiplicative", y)
    assert abs(gap) > 0.02
