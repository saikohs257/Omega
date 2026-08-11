from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow
from tools.dvqt_falsifier import find_projection_collisions


def test_exact_dvqt_collision_exposes_missing_B():
    # The two present states are identical in D,V,q,tau.  B differs, and the
    # existing transition law permits PRECURSOR->EXCITATION only when B>0.
    rows = [
        TelemetryRow(B=0.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=1.0, V=0.4, D=0.2, mode=TiamatMode.EXCITATION, tau_mode=0.0),
        TelemetryRow(B=0.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=3.0),
        TelemetryRow(B=0.0, V=0.4, D=0.2, mode=TiamatMode.PRECURSOR, tau_mode=4.0),
    ]

    collisions = find_projection_collisions(rows)

    assert collisions
    collision = collisions[0]
    assert collision.key == (0.2, 0.4, TiamatMode.PRECURSOR, 3.0)
    assert set(collision.next_modes) == {
        TiamatMode.EXCITATION.value,
        TiamatMode.PRECURSOR.value,
    }
