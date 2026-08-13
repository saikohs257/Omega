import pandas as pd

from experiments.tiamat_head_ablation_battery import assign_seats, build_target


def test_historical_head_seat_partition_contract() -> None:
    rows = []
    for i in range(20):
        rows.append(
            {
                "open_time": pd.Timestamp("2024-01-01") + pd.Timedelta(hours=i),
                "entry_path": "0_to_4" if i == 0 else ("none" if i == 15 else "0_to_4"),
                "SimpleShock": 0.4,
                "LiveDeficit": 0.5,
                "RecoveryWeakness_v1": 0.2,
                "hazard_raw": 1.0,
                "episode_age_h": float(i + 1),
            }
        )
    df = pd.DataFrame(rows)
    df["survive15"] = build_target(df)
    df = assign_seats(df)
    assert df.loc[0, "seat"] == "H0"
    assert set(df.loc[1:14, "seat"].dropna()) == {"H4"}
    assert df.loc[15, "seat"] is None


def test_target_requires_contiguous_active_hours() -> None:
    rows = []
    for i in range(20):
        rows.append(
            {
                "open_time": pd.Timestamp("2024-01-01") + pd.Timedelta(hours=i),
                "entry_path": "0_to_4" if i < 19 else "none",
            }
        )
    df = pd.DataFrame(rows)
    target = build_target(df, hours=3)
    assert target.iloc[0] == 1.0
    assert target.iloc[15] == 0.0
