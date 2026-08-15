from pathlib import Path

import pandas as pd

from experiments.audit_layer1_causal_clearance import audit


SOURCE = Path("data/canonical/layer1_structured_hazard_arm_timeseries(15).csv")


def test_layer1_clearance_contract():
    if not SOURCE.exists():
        return
    result = audit(SOURCE)
    assert result["rows"] == 43848
    assert result["h3_start_count"] == 169
    assert result["hazard_quarantine"] == ["hazard_raw", "hazard_score", "hazard_bucket"]
    assert result["hindsight_quarantine"] == [
        "Crash72", "entry_path", "episode_age_h", "duration_bucket", "episode_type"
    ]
    assert result["feature_clearance"]["promotion_allowed"] is False
