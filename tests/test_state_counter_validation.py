import math

import pytest

from erk import EpistemicState


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, 1.5, True, -1])
def test_normalized_state_counters_require_nonnegative_integers(value) -> None:
    with pytest.raises(ValueError):
        EpistemicState(active_branches=value).normalized()
    with pytest.raises(ValueError):
        EpistemicState(evidence_count=value).normalized()
    with pytest.raises(ValueError):
        EpistemicState(unsupported_depth=value).normalized()


def test_normalized_state_counters_accept_integral_values() -> None:
    state = EpistemicState(
        active_branches=3.0,
        evidence_count=4,
        unsupported_depth=5.0,
    ).normalized()

    assert state.active_branches == 3
    assert state.evidence_count == 4
    assert state.unsupported_depth == 5
