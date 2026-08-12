from __future__ import annotations

import numpy as np
import pytest

from tools.relationship_map import _directional_gap, map_relationships


def test_directional_gap_detects_temporal_order_not_operand_order():
    a = np.zeros(12)
    b = np.zeros(12)
    y = np.zeros(12, dtype=int)
    a[4] = 1.0
    b[5] = 1.0
    y[4] = 1

    gap = _directional_gap(a, b, "and", y)
    assert gap > 0.20


def test_directional_gap_has_no_wraparound_future_leakage():
    a = np.zeros(8)
    b = np.zeros(8)
    y = np.zeros(8, dtype=int)
    b[-1] = 1.0
    y[0] = 1

    gap = _directional_gap(a, b, "and", y)
    assert gap == 0.0


def test_relationship_map_requires_equal_length_inputs():
    with pytest.raises(ValueError, match="same length"):
        map_relationships({"a": [0, 1, 0], "b": [0, 1]}, [0, 1, 0])
