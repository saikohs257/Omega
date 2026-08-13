from __future__ import annotations

import numpy as np
import pandas as pd

from tiamat.historical_hf8 import (
    build_age_chain,
    compute_hinge,
    entry_path_at_start,
    recovered_active_mask,
)


def test_entry_path_thresholds_and_prior_shock_clamp() -> None:
    assert entry_path_at_start(0.70, 0.0) == "0_to_4"
    assert entry_path_at_start(0.85, 0.0) == "2_to_4"
    assert entry_path_at_start(0.86, 0.0) == "3_to_4"
    assert entry_path_at_start(0.90, 0.51) == "2_to_4"


def test_recovered_active_machine_is_stateful_and_exit_precedes_new_start() -> None:
    # The historical exit rule needs six hours of prior shock context.  At
    # hour 7 we deliberately make exit and a fresh start eligible together;
    # exit must win.  Hour 8 can then start the new active interval.
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
