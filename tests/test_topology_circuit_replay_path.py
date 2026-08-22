from atlas.topology_contract import TopologyWitness
from runtime.replay import ReplayEngine
from runtime.state_vector import StateVector
from tesseract.circuit_capsule import CircuitTraceCapsule
from tesseract.circuit_replay import register_circuit_trace
from tesseract.strict_circuit import build_strict_row
from tesseract.topology_circuit_bridge import assert_witness_covers_edge


def test_topology_to_circuit_to_replay_is_explicit_and_deterministic() -> None:
    witness = TopologyWitness(
        atlas_dimension=4,
        coordinates=((0, 0, 0, 0),),
        relations=((("0101", "1101"), "q4"),),
        simplices=(),
    )
    assert_witness_covers_edge(witness, "0101", "1101")

    row = build_strict_row(
        "0101",
        "1101",
        amp_current_residual=2.0,
        residual_voltage_to_edge=3.0,
        edge_release_count=9.0,
        risk_set_count=90.0,
        release_state="RELEASE_OPEN_NOW",
        continuity_prior=1.0,
        capacitance_lock=1.0,
    )
    capsule = CircuitTraceCapsule.from_row(row)
    record = capsule.to_constitutional_record()

    engine = ReplayEngine()
    register_circuit_trace(engine.registry)
    result = engine.replay((record,), StateVector())

    assert result.state_vector["last_record_type"] == "TESSERACT_CIRCUIT_TRACE"
    assert result.state_vector["tesseract_circuit_identity"] == capsule.identity.digest
    assert result.state_vector["tesseract_circuit_row"]["edge_id"] == "0101->1101"
    assert result.state_vector["tesseract_circuit_row"]["runtime_allowed"] is False
