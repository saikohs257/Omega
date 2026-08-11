from tools.dvqt_canonical_corpus import canonical_worlds
from tools.dvqt_tournament import tournament


def test_canonical_corpus_populates_all_projections():
    worlds = canonical_worlds()
    assert len(worlds) == 19
    assert all(len(rows) == 12 for rows in worlds.values())

    result = tournament(worlds)
    for projection in ("DVQT", "DVQT+B", "DVQ+B", "DV+B"):
        metrics = result["metrics"][projection]
        assert metrics["coverage"] > 0
        assert metrics["brier"] == metrics["brier"]
        assert metrics["log_loss"] == metrics["log_loss"]
        assert metrics["auc"] == metrics["auc"]
        assert metrics["pr_auc"] == metrics["pr_auc"]
