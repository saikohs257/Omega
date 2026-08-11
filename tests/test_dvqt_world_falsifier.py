from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow
from tools.dvqt_world_falsifier import analyze_worlds, find_projection_collisions


def test_collision_with_B_variation_is_reported():
    # Two identical DVQT states, differing only in B, with different next modes.
    rows = [
        TelemetryRow(B=0.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=0.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=1.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=1.0, V=0.4, D=0.2, mode=TiamatMode.EXCITATION, tau_mode=3.0),
    ]
    collisions = find_projection_collisions(rows)
    assert len(collisions) == 1
    assert collisions[0].is_non_deterministic
    assert collisions[0].distinct_B == (0.0, 1.0)


def test_world_summary_separates_B_explained_from_unexplained():
    world = [
        TelemetryRow(B=0.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=0.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=1.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=1.0, V=0.4, D=0.2, mode=TiamatMode.EXCITATION, tau_mode=3.0),
    ]
    summary = analyze_worlds({"fixture": world})
    assert summary["total_collisions"] == 1
    assert summary["collisions_with_B_variation"] == 1
    assert summary["collisions_without_B_variation"] == 0
