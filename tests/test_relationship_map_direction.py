import numpy as np

from tools.relationship_map import _directional_gap


def test_directional_gap_can_be_nonzero_for_temporal_order():
    # Construct a deliberately directional toy signal: b_{t+1} tracks a_t,
    # while a_{t+1} does not track b_t. The old operand-swap test would be
    # blind to this because the interaction operators are commutative.
    a = np.array([0, 1, 0, 1, 0, 1, 0, 1], dtype=float)
    b = np.array([0, 0, 1, 0, 1, 0, 1, 0], dtype=float)
    y = np.array([0, 1, 0, 1, 0, 1, 0], dtype=int)
    gap = _directional_gap(a, b, "and", y)
    assert abs(gap) > 0.0
