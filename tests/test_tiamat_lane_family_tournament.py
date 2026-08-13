from experiments.tiamat_lane_family_tournament import FAMILIES, HEADS

def test_expected_heads_and_families():
    assert set(HEADS) == {"H0", "H2", "H3", "H4"}
    assert {"BURDEN", "HAZARD", "SHOCK", "RECOVERY", "AGE"} <= set(FAMILIES)

