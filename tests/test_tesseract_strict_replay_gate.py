from bentaxis.identity import Identity
from runtime.constitutional_record import ConstitutionalRecord
from runtime.replay import ReplayEngine
from runtime.state_vector import StateVector
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
    row = build_strict_row(
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
    record = _record(row)
    replay = ReplayEngine().replay((record,), StateVector())
    assert replay.state_vector.get("last_record_type") == "tesseract_circuit_strict_row"
    assert replay.state_vector.get("last_payload") == row.canonical_payload
