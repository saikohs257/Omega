from tiamat.dvb_benchmark import BenchmarkRow, compare_dvb_history
from tiamat.state import TiamatState


def test_canonical_state_trajectory_preserves_dvb_and_memory():
    states = [
        TiamatState(B=0.10, V=-0.20, D=0.20, tau_D=1.0, tau_mode=0.0),
        TiamatState(B=0.20, V=0.10, D=0.35, tau_D=2.0, tau_mode=1.0),
        TiamatState(B=0.40, V=0.20, D=0.50, tau_D=3.0, tau_mode=2.0),
        TiamatState(B=0.70, V=0.35, D=0.65, tau_D=4.0, tau_mode=3.0),
        TiamatState(B=0.80, V=0.45, D=0.75, tau_D=5.0, tau_mode=4.0),
    ]
    # Keep both classes in the post-horizon portion of the trajectory.
    targets = [0, 0, 1, 0, 1]
    rows = [BenchmarkRow.from_state(state, target) for state, target in zip(states, targets)]
    result = compare_dvb_history(rows, horizon=2)
    assert {item.name for item in result} == {
        "B_history_2", "V_history_2", "D_history_2", "DVB_history_2"
    }


def test_history_benchmark_is_trajectory_only_and_does_not_fit_parameters():
    states = [
        TiamatState(B=0.10, V=0.0, D=0.10, tau_D=0.0, tau_mode=0.0),
        TiamatState(B=0.20, V=0.1, D=0.20, tau_D=1.0, tau_mode=1.0),
        TiamatState(B=0.30, V=0.2, D=0.30, tau_D=2.0, tau_mode=2.0),
        TiamatState(B=0.80, V=0.4, D=0.80, tau_D=3.0, tau_mode=3.0),
    ]
    rows = [BenchmarkRow.from_state(s, y) for s, y in zip(states, [0, 0, 1, 1])]
    result = compare_dvb_history(rows, horizon=1)
    assert all(item.n == 3 for item in result)
