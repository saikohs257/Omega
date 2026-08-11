from tiamat.dvqt_reduction import compare, reduce_row
from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow


def row(*, D=0.0, V=0.0, mode=TiamatMode.QUIESCENT, tau_mode=0.0, timestamp=None):
    return TelemetryRow(D=D, V=V, mode=mode, tau_mode=tau_mode, timestamp=timestamp)


def test_reduce_row_is_exact_projection():
    reduced = reduce_row(row(D=0.7, V=-0.2, mode=TiamatMode.RELAXATION, tau_mode=12.0))
    assert reduced.D == 0.7
    assert reduced.V == -0.2
    assert reduced.q is TiamatMode.RELAXATION
    assert reduced.tau == 12.0


def test_compare_records_transition_disagreement():
    rows = [
        row(timestamp="2026-01-01T00:00:00"),
        row(V=0.2, mode=TiamatMode.PRECURSOR, tau_mode=0.0, timestamp="2026-01-01T01:00:00"),
        row(V=0.2, mode=TiamatMode.EXCITATION, tau_mode=0.0, timestamp="2026-01-01T02:00:00"),
    ]
    result = compare(rows)
    assert result.version == "dvqt-v1"
    assert result.rows == 3
    assert result.agreement_rate >= 0.0
    assert isinstance(result.disagreements, tuple)


def test_compare_does_not_mutate_rows():
    rows = [row(), row(V=0.1, mode=TiamatMode.PRECURSOR)]
    before = tuple(r.to_mapping() for r in rows)
    compare(rows)
    after = tuple(r.to_mapping() for r in rows)
    assert before == after
