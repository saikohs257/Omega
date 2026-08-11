from __future__ import annotations

from tiamat.state_cartography_forensics import run


def test_world_forensics_reports_evidence_status_for_primary_cases():
    rows = {row["world"]: row for row in run()}
    for name in (
        "near_miss",
        "decelerating",
        "proximity_with_resistance",
        "overshoot",
        "reversal_after_acceleration",
    ):
        row = rows[name]
        assert row["similar_state_pairs"] > 0
        assert row["divergent_futures"] >= 0
        assert row["evidence_status"] in {
            "DISCOVERED",
            "INSUFFICIENT_EVIDENCE",
            "NO_PRE_DIVERGENCE_EXPLANATION",
        }


def test_world_forensics_preserves_known_discoveries():
    rows = {row["world"]: row for row in run()}
    assert rows["overshoot"]["evidence_status"] == "DISCOVERED"
    assert rows["overshoot"]["candidates"][0][0] == "hysteresis"
    assert rows["reversal_after_acceleration"]["evidence_status"] == "DISCOVERED"
    assert rows["reversal_after_acceleration"]["candidates"][0][0] == "phase"


def test_world_forensics_marks_missing_evidence_explicitly():
    rows = {row["world"]: row for row in run()}
    for name in ("near_miss", "decelerating", "proximity_with_resistance"):
        assert rows[name]["evidence_status"] == "INSUFFICIENT_EVIDENCE"
