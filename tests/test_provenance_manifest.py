from runtime.provenance_manifest import ProvenanceManifest


def make_manifest(implementation_id: str = "impl-1") -> ProvenanceManifest:
    return ProvenanceManifest(
        corpus_id="corpus-1",
        information_set_id="info-1",
        hypothesis_id="H1",
        implementation_id=implementation_id,
        metric_contract_id="metric-1",
        output_contract_id="output-1",
    )


def test_manifest_identity_is_deterministic() -> None:
    assert make_manifest().manifest_id == make_manifest().manifest_id


def test_manifest_identity_changes_when_implementation_changes() -> None:
    assert make_manifest("impl-1").manifest_id != make_manifest("impl-2").manifest_id
