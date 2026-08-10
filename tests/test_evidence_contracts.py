from runtime.evidence import CorpusIdentity, MetricContract


def test_corpus_identity_is_content_addressed() -> None:
    left = CorpusIdentity(
        corpus_name="layer1",
        corpus_hash="abc123",
        source_ids=("source-b", "source-a"),
        preprocessing_id="prep-v1",
    )
    right = CorpusIdentity(
        corpus_name="layer1",
        corpus_hash="abc123",
        source_ids=("source-a", "source-b"),
        preprocessing_id="prep-v1",
    )

    assert left.corpus_id == right.corpus_id


def test_corpus_identity_changes_when_evidence_changes() -> None:
    left = CorpusIdentity("layer1", "abc123", preprocessing_id="prep-v1")
    right = CorpusIdentity("layer1", "def456", preprocessing_id="prep-v1")

    assert left.corpus_id != right.corpus_id


def test_metric_contract_is_content_addressed() -> None:
    left = MetricContract("auc", parameters=(("positive_label", 1),))
    right = MetricContract("auc", parameters=(("positive_label", 1),))

    assert left.metric_contract_id == right.metric_contract_id


def test_metric_contract_changes_when_semantics_change() -> None:
    higher = MetricContract("error", direction="lower_is_better")
    lower = MetricContract("error", direction="higher_is_better")

    assert higher.metric_contract_id != lower.metric_contract_id
