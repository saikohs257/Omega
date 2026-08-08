from tiamat.identification_registry import (
    CANONICAL_THRESHOLDS,
    DAMPING_REGISTRY,
    DYNAMICS_REGISTRY,
    FORCING_REGISTRY,
    MODEL_REGISTRY,
    RECOVERY_REGISTRY,
    RETIRED_CONTROLS,
)


def test_permanent_model_ids_are_complete_and_unique():
    assert tuple(MODEL_REGISTRY) == tuple(f"M{i}" for i in range(8))
    assert len(MODEL_REGISTRY) == len(set(MODEL_REGISTRY))
    assert MODEL_REGISTRY["M3"].state == ("B", "V", "D")
    assert MODEL_REGISTRY["M7"].role == "permanent V6 control"


def test_equation_registries_are_permanent_namespaces():
    assert tuple(DYNAMICS_REGISTRY) == ("D0", "D1", "D2", "D3", "D4")
    assert tuple(RECOVERY_REGISTRY) == ("R0", "R1", "R2", "R3", "R4")
    assert tuple(DAMPING_REGISTRY) == ("V0", "V1", "V2", "V3")
    assert tuple(FORCING_REGISTRY) == ("F0", "F1")


def test_canonical_control_constants():
    assert CANONICAL_THRESHOLDS == {
        "hazard_low": 0.343,
        "hazard_medium": 0.599,
        "hazard_high": 0.794,
        "refractory_dormancy": 0.95,
    }
    assert "fixed_6h_choke_timer" in RETIRED_CONTROLS
