import numpy as np

from tools.relationship_map import _directional_gap


def test_directional_gap_can_be_nonzero_for_temporal_order():
    # Build labels directly from A_t AND B_{t+1}; the reverse temporal
    # ordering is an independent signal, so this fixture tests direction
    # rather than operand symmetry.
    rng = np.random.default_rng(12345)
    a = rng.integers(0, 2, size=128).astype(float)
    b = rng.integers(0, 2, size=128).astype(float)
    y = (a[:-1].astype(bool) & b[1:].astype(bool)).astype(int)
    gap = _directional_gap(a, b, "and", np.r_[y, 0])
    assert gap > 0.20
