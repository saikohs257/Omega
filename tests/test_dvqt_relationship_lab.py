from tools.dvqt_canonical_tournament import build_worlds
from tools.dvqt_relationship_lab import signals, target_labels
from tools.relationship_map import map_relationships


def test_relationship_lab_covers_all_dvqt_components():
    rows = build_worlds()["world_01"]
    results = map_relationships(signals(rows), target_labels(rows), phase=[r.tau_mode for r in rows[:-1]])
    pairs = {tuple(sorted((r.left, r.right))) for r in results}
    assert pairs == {
        ("B", "D"), ("B", "V"), ("D", "V"),
        ("B", "mode"), ("D", "mode"), ("V", "mode"),
        ("B", "tau"), ("D", "tau"), ("V", "tau"), ("mode", "tau"),
    }


def test_additive_dvqt_world_has_no_large_interaction_synergy():
    rows = build_worlds()["world_01"]
    results = map_relationships(signals(rows), target_labels(rows))
    assert max(r.interaction_gain for r in results) < 0.15
