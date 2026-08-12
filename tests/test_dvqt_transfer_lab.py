from types import SimpleNamespace

import pytest

from tools.dvqt_transfer_lab import circular_null_gains, normalized_gain, run_pair


class _Mode:
    def __init__(self, value: str):
        self.value = value


def _rows(scale: float = 1.0):
    rows = []
    for t in range(48):
        d = scale * ((t % 6) / 5.0)
        v = scale * (((t - 1) % 6) / 5.0)
        rows.append(SimpleNamespace(D=d, V=v, B=0.0, tau_mode=1.0, mode=_Mode("E" if t % 2 else "R")))
    return rows


def test_normalized_gain_is_scale_invariant():
    rows_a = _rows(1.0)
    rows_b = _rows(1000.0)
    x_a = [r.D for r in rows_a[:-1]]
    z_a = [r.V for r in rows_a[:-1]]
    y_a = [rows_a[i + 1].V for i in range(len(rows_a) - 1)]
    x_b = [r.D for r in rows_b[:-1]]
    z_b = [r.V for r in rows_b[:-1]]
    y_b = [rows_b[i + 1].V for i in range(len(rows_b) - 1)]
    assert normalized_gain(x_a, z_a, y_a) == pytest.approx(
        normalized_gain(x_b, z_b, y_b), abs=1e-9
    )


def test_circular_null_preserves_number_of_surrogates():
    result = run_pair("synthetic", _rows(), "D", "V")
    assert result is not None
    assert result.null_n > 0
    assert result.null_mean == pytest.approx(result.null_mean)


def test_transfer_reports_observed_minus_null():
    result = run_pair("synthetic", _rows(), "D", "V")
    assert result is not None
    assert result.excess_gain == pytest.approx(result.observed_gain - result.null_median)


def test_null_is_not_empty_for_valid_history():
    rows = _rows()
    x = [r.D for r in rows[:-1]]
    z = [r.V for r in rows[:-1]]
    y = [rows[i + 1].V for i in range(len(rows) - 1)]
    assert circular_null_gains(x, z, y)
