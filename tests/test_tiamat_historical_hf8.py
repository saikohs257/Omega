from __future__ import annotations

import numpy as np
import pandas as pd

from tiamat.historical_hf8 import (
    build_age_chain,
    build_thehinge,
    compute_hinge,
    entry_path_at_start,
    promote_v41e,
    recovered_active_mask,
)


def test_entry_path_thresholds_and_prior_shock_clamp() -> None:
    assert entry_path_at_start(0.70, 0.0) == "0_to_4"
    assert entry_path_at_start(0.85, 0.0) == "2_to_4"
    assert entry_path_at_start(0.86, 0.0) == "3_to_4"
    assert entry_path_at_start(0.90, 0.51) == "2_to_4"


def test_recovered_active_machine_is_stateful_and_exit_precedes_new_start() -> None:
    idx = pd.date_range("2020-01-01", periods=9, freq="h")
    frame = pd.DataFrame(
        {
            "hazard_raw": [0.0, 1.2, 1.3, 1.3, 1.3, 1.3, 1.3, 2.5, 3.7],
            "hazard_score": [0.2, 0.8, 0.81, 0.82, 0.83, 0.84, 0.85, 0.60, 0.90],
            "LiveDeficit": [0.0, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9],
            "SimpleShock": [0.0, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6],
        },
        index=idx,
    )
    active = recovered_active_mask(frame)
    assert active.tolist() == [False, True, True, True, True, True, True, False, True]


def test_hinge_v3a_combines_tightness_and_age() -> None:
    idx = pd.date_range("2020-01-01", periods=3, freq="D")
    tight = pd.Series([1.0, 2.0, 3.0], index=idx)
    age = pd.Series([3.0, 2.0, 1.0], index=idx)
    got = compute_hinge(tight, age)
    expected = 0.70 * tight + 0.30 * age
    pd.testing.assert_series_equal(got, expected, check_names=False)


def test_age_chain_uses_daily_max_then_7d_mean() -> None:
    idx = pd.date_range("2020-01-01", periods=24 * 8, freq="h")
    ages = pd.Series(np.tile(np.arange(1, 25), 8), index=idx, dtype=float)
    episode_type = pd.Series("mixed", index=idx)
    out = build_age_chain(ages, episode_type)
    assert out.index.freq is not None
    assert float(out.loc[pd.Timestamp("2020-01-08"), "day_max_age_h"]) == 24.0
    assert float(out.loc[pd.Timestamp("2020-01-08"), "age_7d"]) == 24.0


def test_thehinge_promotes_phasic_to_trapped_after_8_hours() -> None:
    idx = pd.date_range("2020-01-01", periods=10, freq="h")
    hourly = pd.DataFrame(
        {
            "hazard_raw": [0.0, 1.2] + [1.3] * 8,
            "hazard_score": [0.2, 0.80] + [0.80] * 8,
            # Previous-hour LD must already be >0.85 so the start enters via
            # 3->4; prior shock remains <=0.50 so the 3->4 -> 2->4 clamp does
            # not fire.
            "LiveDeficit": [0.90, 0.90] + [0.90] * 8,
            "SimpleShock": [0.40, 0.60] + [0.60] * 8,
        },
        index=idx,
    )
    daily = pd.DataFrame(index=pd.date_range("2020-01-01", periods=1, freq="D"))
    out = build_thehinge(hourly, daily)
    assert out["episode_type"].iloc[1] == "phasic"
    assert out["episode_type"].iloc[9] == "trapped"
    assert out["run_age_h"].iloc[9] == 9.0


def test_v41e_gate_preserves_historical_branch_authority() -> None:
    row = {
        "hazard_raw_0_4h_max_from_l1": 4.0,
        "SimpleShock_0_4h_max_from_l1": 0.70,
        "prev_active_exit_SimpleShock": 0.2,
    }
    out = promote_v41e(row)
    assert out["selected"] is True
    assert out["posture"] == "short_watch"
    assert out["authority"] == "canonical_admission_gate"
    assert out["version"] == "v41e_gate_v1"
