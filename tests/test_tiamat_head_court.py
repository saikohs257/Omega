from experiments.tiamat_head_court import HEAD_SCOPE, MODES, score_scope


def test_each_authority_head_has_exact_scoped_transition():
    assert HEAD_SCOPE["H0"] == ("Q", "R")
    assert HEAD_SCOPE["H2"] == ("E", "R")
    assert HEAD_SCOPE["H3"] == ("C", "R")
    assert HEAD_SCOPE["H4"] == ("H", "H")
    assert HEAD_SCOPE["ExitBridge"] == ("R", "Rf")


def test_priorcarry_is_history_not_single_transition():
    assert HEAD_SCOPE["PriorCarry"] == MODES


def test_entry_heads_are_pairwise_distinct():
    assert len({HEAD_SCOPE[h] for h in ("H0", "H2", "H3")}) == 3


def test_scope_court_has_one_legal_transition_for_each_non_memory_head():
    for head in ("H0", "H2", "H3", "H4", "ExitBridge"):
        result = score_scope(head)
        assert result.legal == 1
        assert result.illegal == 48
