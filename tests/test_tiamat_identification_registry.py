import pytest

from tiamat.identification_registry import (
    CANONICAL_THRESHOLDS,
    DAMPING_REGISTRY,
    DYNAMICS_REGISTRY,
    FORCING_REGISTRY,
    MODEL_REGISTRY,
    RECOVERY_REGISTRY,
    RETIRED_CONTROLS,
    model,
)


def test_model_ids_are_permanent_and_complete():
    assert tuple(MODEL_REGISTRY) == ("M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7")
    assert MODEL_REGISTRY["M3"].state == ("B", "V", "D")
    assert "V6" in MODEL_REGISTRY["M7"].role


def test_experimental_law_ids_are_disjoint():
    assert set(DYNAMICS_REGISTRY) == {"D0", "D1", "D2", "D3", "D4"}
    assert set(RECOVERY_REGISTRY) == {"R0", "R1", "R2", "R3", "R4"}
    assert set(DAMPING_REGISTRY) == {"V0", "V1", "V2", "V3"}
    assert set(FORCING_REGISTRY) == {"F0", "F1"}


def test_canonical_thresholds_are_frozen():
    assert CANONICAL_THRESHOLDS == {
        "hazard_low": 0.343,
        "hazard_medium": 0.599,
        "hazard_high": 0.794,
        "refractory_dormancy": 0.95,
    }
    assert "fixed_6h_choke_timer" in RETIRED_CONTROLS


def test_unknown_model_fails_closed():
    with pytest.raises(KeyError):
        model("M8")
