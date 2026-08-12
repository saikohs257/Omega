from tiamat.dvb_benchmark import BenchmarkRow, compare_dvb


def test_dvb_comparison_keeps_all_representations_visible():
    rows = [
        BenchmarkRow(B=0.2, V=-0.3, D=0.2, recovery=0.3, residual_load=0.0, momentum=-0.3, pressure=0.0, hazard_raw=0.2, target=0),
        BenchmarkRow(B=0.4, V=-0.1, D=0.4, recovery=0.1, residual_load=0.3, momentum=-0.1, pressure=0.0, hazard_raw=0.4, target=0),
        BenchmarkRow(B=0.7, V=0.2, D=0.7, recovery=0.0, residual_load=0.7, momentum=0.2, pressure=0.2, hazard_raw=0.9, target=1),
        BenchmarkRow(B=0.9, V=0.4, D=0.8, recovery=0.0, residual_load=0.8, momentum=0.4, pressure=0.4, hazard_raw=1.2, target=1),
    ]
    result = compare_dvb(rows)
    assert [item.name for item in result] == [
        "B", "V", "D", "DVB", "recovery", "residual_load", "momentum", "pressure", "hazard_raw"
    ]
    assert all(item.n == 4 for item in result)


def test_dvb_reduction_is_not_claimed_as_causal_or_canonical():
    rows = [
        BenchmarkRow(B=0.1, V=-0.2, D=0.2, recovery=0.2, residual_load=0.0, momentum=-0.2, pressure=0.0, hazard_raw=0.1, target=0),
        BenchmarkRow(B=0.9, V=0.3, D=0.9, recovery=0.0, residual_load=0.9, momentum=0.3, pressure=0.3, hazard_raw=1.2, target=1),
    ]
    result = compare_dvb(rows)
    assert all(item.separation >= 0.0 for item in result)
