from __future__ import annotations

import pytest

from end.core import CertaintyLevel, Diagnosis, FailureRecord, FailureTaxonomy
from pond.core import LineageStatus, MutationOperation, MutationProposal, PondEntry


def test_failure_record_hash_is_stable_and_sensitive_to_changes() -> None:
    diagnosis = Diagnosis(
        taxonomy=FailureTaxonomy.STRUCTURAL,
        certainty=CertaintyLevel.CONFIRMED,
        summary="missing state variable",
        rationale="the replay cannot be reproduced without a latent recovery state",
        version=2,
        metadata={"source": "archaeology"},
    )
    record_a = FailureRecord(
        failure_id="F-1",
        experiment_id="E-1",
        hypothesis_id="H-1",
        corpus_hash="c1",
        information_set_hash="i1",
        metric_contract_hash="m1",
        implementation_hash="p1",
        outcome="FAIL",
        metrics={"loss": 0.91},
        residuals={"residual": 0.42},
        stratum_results={"bull": {"loss": 0.8}},
        reliability_results={"repeatable": True},
        diagnosis=diagnosis,
        created_at="2026-08-09T00:00:00Z",
    )
    record_b = FailureRecord(
        failure_id="F-1",
        experiment_id="E-1",
        hypothesis_id="H-1",
        corpus_hash="c1",
        information_set_hash="i1",
        metric_contract_hash="m1",
        implementation_hash="p1",
        outcome="FAIL",
        metrics={"loss": 0.91},
        residuals={"residual": 0.42},
        stratum_results={"bull": {"loss": 0.8}},
        reliability_results={"repeatable": True},
        diagnosis=diagnosis,
        created_at="2026-08-09T00:00:00Z",
    )

    assert record_a.to_dict() == record_b.to_dict()
    assert record_a.content_hash() == record_b.content_hash()

    record_c = FailureRecord(
        failure_id="F-1",
        experiment_id="E-1",
        hypothesis_id="H-1",
        corpus_hash="c1",
        information_set_hash="i1",
        metric_contract_hash="m1",
        implementation_hash="p1",
        outcome="FAIL",
        metrics={"loss": 0.12},
        residuals={"residual": 0.42},
        stratum_results={"bull": {"loss": 0.8}},
        reliability_results={"repeatable": True},
        diagnosis=diagnosis,
        created_at="2026-08-09T00:00:00Z",
    )

    assert record_c.content_hash() != record_a.content_hash()


def test_diagnosis_and_taxonomy_defaults_are_explicit() -> None:
    diagnosis = Diagnosis()

    assert diagnosis.taxonomy is FailureTaxonomy.UNKNOWN
    assert diagnosis.certainty is CertaintyLevel.UNKNOWN
    assert diagnosis.to_dict()["version"] == 1
    assert diagnosis.to_dict()["metadata"] == {}


def test_pond_entry_hash_is_stable_and_sensitive_to_proposal_changes() -> None:
    proposal = MutationProposal(
        source_hypothesis="H-1",
        source_failure="F-1",
        diagnosis_id="D-1",
        operation=MutationOperation.SNIP,
        target_component="recovery-law",
        rationale="remove suspected defect",
        expected_effect="reduce residual load",
        metadata={"precommitted": True},
    )
    entry_a = PondEntry(
        hypothesis_id="H-2",
        failure_id="F-1",
        experiment_id="E-1",
        hypothesis_definition_hash="h1",
        provenance_hash="p1",
        parent_id="H-1",
        lineage_id="L-1",
        failure_taxonomy="structural",
        diagnosis_ids=("D-1",),
        mutation_budget=2,
        resurrection_status=LineageStatus.ACTIVE,
        evidence_hashes=("e1", "e2"),
        proposal=proposal,
        metadata={"gate": "A"},
    )
    entry_b = PondEntry(
        hypothesis_id="H-2",
        failure_id="F-1",
        experiment_id="E-1",
        hypothesis_definition_hash="h1",
        provenance_hash="p1",
        parent_id="H-1",
        lineage_id="L-1",
        failure_taxonomy="structural",
        diagnosis_ids=("D-1",),
        mutation_budget=2,
        resurrection_status=LineageStatus.ACTIVE,
        evidence_hashes=("e1", "e2"),
        proposal=proposal,
        metadata={"gate": "A"},
    )

    assert entry_a.to_dict() == entry_b.to_dict()
    assert entry_a.content_hash() == entry_b.content_hash()
    assert entry_a.to_dict()["resurrection_status"] == LineageStatus.ACTIVE.value
    assert entry_a.to_dict()["proposal"]["operation"] == MutationOperation.SNIP.value

    entry_c = PondEntry(
        hypothesis_id="H-2",
        failure_id="F-1",
        experiment_id="E-1",
        hypothesis_definition_hash="h1",
        provenance_hash="p1",
        parent_id="H-1",
        lineage_id="L-1",
        failure_taxonomy="structural",
        diagnosis_ids=("D-1",),
        mutation_budget=2,
        resurrection_status=LineageStatus.ACTIVE,
        evidence_hashes=("e1", "e2"),
        proposal=MutationProposal(
            source_hypothesis="H-1",
            source_failure="F-1",
            diagnosis_id="D-1",
            operation=MutationOperation.ALTER,
            target_component="recovery-law",
            rationale="change suspected defect",
            expected_effect="reduce residual load",
            metadata={"precommitted": True},
        ),
        metadata={"gate": "A"},
    )

    assert entry_c.content_hash() != entry_a.content_hash()


def test_mutation_proposal_is_precommitted_and_serializes_cleanly() -> None:
    proposal = MutationProposal(
        source_hypothesis="H-9",
        source_failure="F-9",
        diagnosis_id="D-9",
        operation=MutationOperation.HOLD,
        created_before_execution=True,
    )

    payload = proposal.to_dict()
    assert payload["created_before_execution"] is True
    assert payload["operation"] == MutationOperation.HOLD.value
    assert payload["metadata"] == {}


def test_enum_values_cover_the_expected_termination_and_unknown_states() -> None:
    assert FailureTaxonomy.UNKNOWN.value == "unknown"
    assert CertaintyLevel.UNKNOWN.value == "UNKNOWN"
    assert LineageStatus.QUARANTINED.value == "QUARANTINED"
    assert MutationOperation.MERGE.value == "MERGE"
