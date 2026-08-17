from pathlib import Path
import pandas as pd

from experiments.tiamat_native_route_extractor_v1 import _episode_blocks


def test_native_start_partition_counts(tmp_path: Path):
    csv = tmp_path / "layer1.csv"
    # Minimal structural check: starts are age==1 and only the three legacy seats qualify.
    pd.DataFrame({
        "open_time": pd.date_range("2024-01-01", periods=8, freq="h"),
        "SimpleShock": [0.5]*8,
        "LiveDeficit": [0.6]*8,
        "hazard_raw": [1.0]*8,
        "entry_path": ["2_to_4","2_to_4","3_to_4","3_to_4","0_to_4","0_to_4","bad","bad"],
        "episode_age_h": [1,2,1,2,1,2,1,2],
        "regime_30d": ["x"]*8,
        "Crash72": [0]*8,
    }).to_csv(csv, index=False)
    out = _episode_blocks(pd.read_csv(csv))
    assert len(out) == 6
    assert out["start_transition_path"].value_counts().to_dict() == {"2_to_4": 2, "3_to_4": 2, "0_to_4": 2}
    assert set(out["topology_path"]) == {"0_to_4","2_to_4","3_to_4"}
    assert set(out["tiamat_head"]) == {"H0_FalseCalmIgnition","H2_ResetDragRelease","H3_RecoveryInversion"}
