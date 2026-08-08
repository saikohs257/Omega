import math

import pytest

from erk.core import PolicyConfig


@pytest.mark.parametrize("field", ["depth_bound", "branch_bound"])
def test_policy_config_rejects_non_finite_bounds(field: str) -> None:
    with pytest.raises(ValueError, match=f"{field} must be finite"):
        PolicyConfig(**{field: math.inf})


@pytest.mark.parametrize("field", ["depth_bound", "branch_bound"])
def test_policy_config_rejects_fractional_bounds(field: str) -> None:
    with pytest.raises(ValueError, match=f"{field} must be an integer"):
        PolicyConfig(**{field: 1.5})


def test_policy_config_accepts_integral_float_bounds() -> None:
    config = PolicyConfig(depth_bound=8.0, branch_bound=16.0)
    assert config.depth_bound == 8
    assert config.branch_bound == 16
