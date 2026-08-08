import pytest

from runtime.state_vector import StateVector


def test_state_vector_copies_and_freezes_input_mapping() -> None:
    source = {"seed": "base"}
    state = StateVector(source)

    source["seed"] = "mutated"
    source["new"] = "outside"

    assert state.get("seed") == "base"
    assert state.get("new") is None

    with pytest.raises(TypeError):
        state.values["seed"] = "inside"


def test_state_vector_rejects_non_mapping_values() -> None:
    with pytest.raises(TypeError, match="values"):
        StateVector([("seed", "base")])
