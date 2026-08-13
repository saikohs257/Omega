"""Contract tests for the recovered TIAMAT head-scope record.

These tests intentionally do not invent head implementations. They lock the
historically recovered topology so later experiments cannot silently broaden
a head's authority domain.
"""
from tiamat.modes import TiamatMode


HEAD_SCOPE = {
    "H0": ("Q", "H"),       # mode 0 -> mode 4
    "H2": ("E", "H"),       # mode 2 -> mode 4
    "H3": ("C", "H"),       # mode 3 -> mode 4 boundary
    "H4": ("H", "H"),       # mode 4 -> mode 4 persistence/release seat
    "ExitBridge": ("H", "Rf"),
    "PriorCarry": ("Q", "P", "E", "C", "H", "R", "Rf"),
}


def test_all_canonical_modes_exist() -> None:
    assert {m.value for m in TiamatMode} == {"Q", "P", "E", "C", "H", "R", "Rf"}


def test_entry_heads_are_scoped_to_distinct_legal_target_H() -> None:
    assert HEAD_SCOPE["H0"] == ("Q", "H")
    assert HEAD_SCOPE["H2"] == ("E", "H")
    assert HEAD_SCOPE["H3"] == ("C", "H")


def test_persistence_and_exit_are_not_entry_heads() -> None:
    assert HEAD_SCOPE["H4"] == ("H", "H")
    assert HEAD_SCOPE["ExitBridge"] == ("H", "Rf")


def test_priorcarry_is_memory_not_a_transition_head() -> None:
    assert len(HEAD_SCOPE["PriorCarry"]) == len(TiamatMode)


def test_diagnostic_components_have_no_authority_scope() -> None:
    # T3 and S2 are deliberately absent: their omission is the contract.
    assert "T3" not in HEAD_SCOPE
    assert "S2" not in HEAD_SCOPE
