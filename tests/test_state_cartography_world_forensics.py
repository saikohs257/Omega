from tiamat.state_cartography_forensics_report import run


def test_world_forensics_reports_divergence_for_primary_cases():
    rows = {row["world"]: row for row in run()}
    for name in (
        "near_miss",
        "decelerating",
        "proximity_with_resistance",
        "overshoot",
        "reversal_after_acceleration",
    ):
        assert rows[name]["similar_state_pairs"] > 0
        assert rows[name]["divergent_futures"] > 0
        assert rows[name]["top_pre_divergence_dimensions"]


def test_world_forensics_has_consistent_control():
    rows = {row["world"]: row for row in run()}
    control = rows["control_consistent"]
    assert control["similar_state_pairs"] > 0
    assert control["divergent_futures"] == 0
    assert control["consistent_futures"] == control["similar_state_pairs"]


def test_forensics_candidate_matches_are_evidence_not_promotions():
    rows = {row["world"]: row for row in run()}
    for row in rows.values():
        assert "expected_missing_dimension" in row
        assert "top_pre_divergence_dimensions" in row
