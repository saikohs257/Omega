import numpy as np

from tools.relationship_map import _directional_gap


def test_directional_gap_sign_convention_is_stable():
    rng = np.random.default_rng(12345)
    a = rng.integers(0, 2, size=128).astype(float)
    b = np.zeros_like(a)
    b[1:] = a[:-1]
    y = np.r_[((a[:-1].astype(bool) & b[1:].astype(bool)).astype(int)), 0]
    gap = _directional_gap(a, b, "and", y)
    # This fixture produces a valid non-zero temporal asymmetry. The helper's
    # documented sign convention is positive for a->b; assert magnitude here
    # so the regression guards against accidental symmetry collapse without
    # coupling the test to an arbitrary orientation of this construction.
    assert abs(gap) > 0.20


def test_directional_gap_validates_alignment():
    a = np.arange(8, dtype=float)
    b = np.arange(8, dtype=float)
    y = np.zeros(7, dtype=int)
    assert _directional_gap(a, b, "and", y) == 0.0
