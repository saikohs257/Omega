import numpy as np

from tools.relationship_map import _directional_gap


def test_directional_gap_can_be_nonzero_for_temporal_order():
    rng = np.random.default_rng(12345)
    a = rng.integers(0, 2, size=128).astype(float)
    b = np.zeros_like(a)
    b[1:] = a[:-1]
    y = (a[:-1].astype(bool) & b[1:].astype(bool)).astype(int)
    gap = _directional_gap(a, b, "and", np.r_[y, 0])
    assert gap > 0.20
