from bentaxis.identity import Identity
from bentaxis.store import BentAxisStore
from runtime.constitutional_record import ConstitutionalRecord
from runtime.replay import ReplayEngine
from runtime.replay_registry import ReplayRegistry
from runtime.state_vector import StateVector
from tesseract.circuit_capsule import CircuitTraceCapsule
from tesseract.circuit_replay import register_circuit_trace
from tesseract.strict_circuit import StrictCircuitRow, build_strict_row, assert_reference_authority


def _record(row: StrictCircuitRow) -> ConstitutionalRecord:
    return ConstitutionalRecord(
        record_type="tesseract_circuit_strict_row",
        payload=row.canonical_payload,
        identity_refs=(Identity.calculate(row.canonical_payload).digest,),
        jurisdiction="tesseract-reference",
        provenance=(("source", "TESSERACT_CIRCUIT_V1_1_COMPONENT_FREEZE_20260628"),),
        timestamp="0",
    )


def _row() -> StrictCircuitRow:
    return build_strict_row(
        "0000",
        "0010",
        amp_current_residual=1.5,
        residual_voltage_to_edge=2.5,
        edge_release_count=2,
        risk_set_count=20,
        release_state="RELEASE_PENDING_1_6H",
        continuity_prior=0.75,
        capacitance_lock=0.5,
    )


def test_strict_row_uses_frozen_hand_built_rule() -> None:
    row = build_strict_row(
        "0000",
        "0001",
        amp_current_residual=2.0,
        residual_voltage_to_edge=3.0,
        edge_release_count=9,
        risk_set_count=90,
        release_state="RELEASE_OPEN_NOW",
        continuity_prior=1.0,
        capacitance_lock=1.0,
    )
    assert row.changed_axis == 3
    assert row.conductance == 10.0 / 100.0
    assert row.ohms == 1.0 / (1e-6 + 0.1)
    assert row.release_permission == 1.0
    assert_reference_authority(row)


def test_strict_row_rejects_runtime_authority() -> None:
    row = build_strict_row(
        "0000",
        "0001",
        amp_current_residual=1.0,
        residual_voltage_to_edge=1.0,
        edge_release_count=1,
        risk_set_count=10,
        release_state="HOLD_LOCKED",
        continuity_prior=1.0,
        capacitance_lock=1.0,
        runtime_allowed=False,
    )
    assert row.authority_state == "RESEARCH_CANDIDATE"
    assert not row.runtime_allowed


def test_strict_row_replay_preserves_canonical_payload() -> None:
    row = _row()
    record = _record(row)
    replay = ReplayEngine().replay((record,), StateVector())
    assert replay.state_vector.get("last_record_type") == "tesseract_circuit_strict_row"
    assert replay.state_vector.get("last_payload") == row.canonical_payload


def test_circuit_trace_capsule_crosses_bentaxis_without_authority() -> None:
    capsule = CircuitTraceCapsule.from_row(_row())
    store = BentAxisStore()
    stored = capsule.append_to(store)
    assert stored.identity.digest == Identity.calculate(
        {"kind": stored.event.kind, "payload": stored.event.payload, "metadata": stored.event.metadata}
    ).digest
    assert store.verify_integrity()
    snapshot = capsule.bentaxis_snapshot(store)
    assert snapshot.canonical_hash() == snapshot.canonical_hash()
    assert capsule.row.runtime_allowed is False
    assert capsule.row.authority_state == "RESEARCH_CANDIDATE"


def test_capsule_identity_changes_when_strict_row_changes() -> None:
    first = CircuitTraceCapsule.from_row(_row())
    second = CircuitTraceCapsule.from_row(
        build_strict_row(
            "0000",
            "0010",
            amp_current_residual=1.6,
            residual_voltage_to_edge=2.5,
            edge_release_count=2,
            risk_set_count=20,
            release_state="RELEASE_PENDING_1_6H",
            continuity_prior=0.75,
            capacitance_lock=0.5,
        )
    )
    assert first.identity.digest != second.identity.digest


def test_capsule_rejects_runtime_authority() -> None:
    row = _row()
    object.__setattr__(row, "runtime_allowed", True)
    try:
        CircuitTraceCapsule.from_row(row)
    except ValueError as exc:
        assert "runtime authority" in str(exc)
    else:
        raise AssertionError("runtime authority must remain forbidden")


def test_circuit_trace_uses_specific_replay_operator() -> None:
    capsule = CircuitTraceCapsule.from_row(_row())
    record = capsule.to_constitutional_record()
    registry = ReplayRegistry()
    register_circuit_trace(registry)
    replay = ReplayEngine(registry=registry).replay((record,), StateVector())
    assert replay.state_vector.get("tesseract_circuit_identity") == capsule.identity.digest
    assert replay.state_vector.get("tesseract_circuit_row") == capsule.row.canonical_payload


def test_circuit_trace_replay_rejects_authority_escalation() -> None:
    capsule = CircuitTraceCapsule.from_row(_row())
    payload = dict(capsule.to_constitutional_record().payload)
    row = dict(payload["row"])
    row["runtime_allowed"] = True
    payload["row"] = row
    record = ConstitutionalRecord(
        record_type="TESSERACT_CIRCUIT_TRACE",
        payload=payload,
        identity_refs=(capsule.identity.digest,),
    )
    registry = ReplayRegistry()
    register_circuit_trace(registry)
    try:
        ReplayEngine(registry=registry).replay((record,), StateVector())
    except ValueError as exc:
        assert "runtime-authorized" in str(exc)
    else:
        raise AssertionError("replay must reject authority escalation")
