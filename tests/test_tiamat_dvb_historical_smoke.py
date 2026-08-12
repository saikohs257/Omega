from tiamat.dvb_benchmark import BenchmarkRow, compare_dvb
from tiamat.dynamics import DynamicsSnapshot


def _row(target: int, B: float, V: float, D: float) -> BenchmarkRow:
    recovery = max(0.0, -V)
    pressure = max(0.0, V)
    return BenchmarkRow(
        B=B,
        V=V,
        D=D,
        recovery=recovery,
        residual_load=max(0.0, D - recovery),
        momentum=V,
        pressure=pressure,
        hazard_raw=D + pressure,
        target=target,
    )


def test_dvb_representations_run_on_tiamat_dynamics_outputs() -> None:
    snapshots = [
        DynamicsSnapshot(0.2, 0.25, 0.10, 0.0, 0.25, 0.25, 0.30, 0.18),
        DynamicsSnapshot(0.4, 0.45, 0.35, 0.0, 0.45, 0.45, 0.80, 0.73),
        DynamicsSnapshot(0.3, 0.10, 0.20, 0.10, 0.10, 0.10, 0.30, 0.18),
        DynamicsSnapshot(0.7, 0.75, 0.70, 0.0, 0.75, 0.75, 1.45, 0.41),
    ]
    rows = [
        _row(0, 0.2, 0.25, 0.10),
        _row(1, 0.4, 0.45, 0.35),
        _row(0, 0.3, 0.10, 0.20),
        _row(1, 0.7, 0.75, 0.70),
    ]
    result = compare_dvb(rows)
    assert len(result) == 9
    assert {item.name for item in result} == {
        "B", "V", "D", "DVB", "recovery", "residual_load",
        "momentum", "pressure", "hazard_raw"
    }
    assert all(item.n == len(snapshots) for item in result)
