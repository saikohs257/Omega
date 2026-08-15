from pathlib import Path

from experiments.audit_layer1_causal_clearance import (
    EXPECTED_H3_STARTS,
    EXPECTED_ROWS,
    EXPECTED_SOURCE_SHA256,
    HAZARD_QUARANTINE,
    HINDSIGHT_QUARANTINE,
    RUNTIME_CANDIDATES,
    audit,
)


SOURCE = Path("data/canonical/layer1_structured_hazard_arm_timeseries(15).csv")


def test_layer1_clearance_contract():
    assert SOURCE.exists(), "canonical Layer-1 source is required; do not silently skip the integrity gate"
    result = audit(SOURCE)
    assert result["rows"] == EXPECTED_ROWS
    assert result["h3_start_count"] == EXPECTED_H3_STARTS
    assert result["source_sha256"] == EXPECTED_SOURCE_SHA256
    assert result["runtime_candidates"] == RUNTIME_CANDIDATES
    assert result["hazard_quarantine"] == HAZARD_QUARANTINE
    assert result["hindsight_quarantine"] == HINDSIGHT_QUARANTINE
    assert result["hourly_cadence_verified"] is True
    assert result["feature_clearance"]["promotion_allowed"] is False
