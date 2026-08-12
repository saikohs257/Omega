from types import SimpleNamespace

import pytest

from tools.dvqt_transfer_lab import run_pair


class _Mode:
    def __init__(self, value: str):
        self.value = value


def _rows(scale: float = 1.0):
    rows = []
    for t in range(32):
        d = scale * ((t % 4) / 3.0)
        # V is mostly a lagged copy of D; its own current history is weaker
        # than D's present signal for predicting the next V.
        v = scale * (((t - 1) % 4) / 3.0)
        rows.append(SimpleNamespace(D=d, V=v, B=0.0, tau_mode=1.0, mode=_Mode("E" if t % 2 else "R")))
    return rows


def test_transfer_gain_is_scale_invariant():
    a = run_pair("synthetic", _rows(1.0), "D", "V")
    b = run_pair("synthetic", _rows(1000.0), "D", "V")
    assert a is not None and b is not None
    assert a.normalized_gain == pytest.approx(b.normalized_gain, abs=1e-9)


def test_transfer_gain_is_conditional_on_destination_history():
    result = run_pair("synthetic", _rows(), "D", "V")
    assert result is not None
    assert result.dst_history_mse >= 0.0
    assert result.joint_mse >= 0.0
    assert result.normalized_gain == pytest.approx(
        result.raw_gain / max(result.dst_history_mse, 1e-12)
    )
