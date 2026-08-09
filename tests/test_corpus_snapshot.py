from __future__ import annotations

import pytest

from tiamat.corpus_snapshot import CorpusSnapshot


def test_snapshot_freezes_mapping_values_and_verifies():
    source = [{"timestamp": "2026-01-01T00:00:00Z", "mode": "Q", "value": 1}]
    snapshot = CorpusSnapshot.freeze(source)
    source[0]["value"] = 99

    snapshot.verify()
    assert snapshot.rows[0]["value"] == 1


def test_snapshot_rejects_empty_corpus():
    with pytest.raises(ValueError, match="empty corpus"):
        CorpusSnapshot.freeze([])


def test_snapshot_detects_internal_mutation():
    snapshot = CorpusSnapshot.freeze([{"mode": "Q", "value": 1}])
    snapshot.rows[0]["value"] = 2

    with pytest.raises(ValueError, match="snapshot has changed"):
        snapshot.verify()
