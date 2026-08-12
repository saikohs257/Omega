import pytest

from tiamat.dvb_benchmark import BenchmarkRow, compare_dvb, compare_dvb_history
from tiamat.state import TiamatState


def _state(B: float, V: float, D: float, tau_D: float = 0.0, tau_mode: float = 0.0) -> TiamatState:
    return TiamatState(B=B, V=V, D=D, tau_D=tau_D, tau_mode=tau_mode)


def test_dvb_benchmark_consumes_canonical_tiamat_state() -> None:
    states = [
        _state(0.20, 0.25, 0.10),
        _state(0.40, 0.45, 0.35, 1.0),
        _state(0.30, 0.10, 0.20, 2.0),
        _state(0.70, 0.75, 0.70, 3.0, 1.0),
    ]
    rows = [
        BenchmarkRow.from_state(states[0], 0),
        BenchmarkRow.from_state(states[1], 1),
        BenchmarkRow.from_state(states[2], 0),
        BenchmarkRow.from_state(states[3], 1),
    ]
    result = compare_dvb(rows)
    assert {item.name for item in result} == {
        "B", "V", "D", "DVB", "recovery", "residual_load",
        "momentum", "pressure", "hazard_raw"
    }
    assert all(item.n == len(states) for item in result)


def test_dvb_temporal_accumulation_is_separate_from_instantaneous_score() -> None:
    states = [
        _state(0.10, 0.05, 0.10),
        _state(0.15, 0.10, 0.15, 1.0),
        _state(0.20, 0.20, 0.20, 2.0),
        _state(0.25, 0.30, 0.25, 3.0),
        _state(0.30, 0.40, 0.30, 4.0),
        _state(0.35, 0.50, 0.35, 5.0),
    ]
    rows = [BenchmarkRow.from_state(state, i % 2) for i, state in enumerate(states)]
    result = compare_dvb_history(rows, horizon=2)
    assert {item.name for item in result} == {
        "B_history_2", "V_history_2", "D_history_2", "DVB_history_2"
    }
    assert all(item.n == 4 for item in result)


def test_mapping_adapter_preserves_canonical_dvb_values() -> None:
    row = {"B": 0.4, "V": -0.2, "D": 0.7, "tau_D": 4.0, "target": 1}
    adapted = BenchmarkRow.from_mapping(row)
    assert adapted.B == 0.4
    assert adapted.V == -0.2
    assert adapted.D == 0.7
    assert adapted.recovery == 0.2
    assert adapted.residual_load == pytest.approx(0.5)
    assert adapted.target == 1
