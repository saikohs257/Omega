from __future__ import annotations

from tiamat.model_selection import CandidateSpec, ModelSelector, evaluate_candidate


def test_causal_candidate_improves_brier_and_auc() -> None:
    labels = (0, 0, 0, 1, 1, 1)
    # Deliberately weak/inverted baseline so the causal candidate must
    # demonstrate a real discrimination improvement rather than merely
    # matching an already-perfect ranking.
    base = (0.65, 0.60, 0.55, 0.45, 0.40, 0.35)
    causal = (0.05, 0.10, 0.15, 0.85, 0.90, 0.95)
    a = evaluate_candidate(CandidateSpec("base", ("damage",)), base, labels)
    b = evaluate_candidate(CandidateSpec("charge", ("charge",)), causal, labels)
    assert b.auc > a.auc
    assert b.brier < a.brier
    assert b.log_loss < a.log_loss


def test_irrelevant_candidate_is_not_needed_for_selection() -> None:
    labels = (0, 0, 0, 1, 1, 1)
    useful = evaluate_candidate(
        CandidateSpec("core", ("damage", "momentum")),
        (0.05, 0.10, 0.15, 0.85, 0.90, 0.95),
        labels,
    )
    irrelevant = evaluate_candidate(
        CandidateSpec("noise", ("orbit",)),
        (0.49, 0.51, 0.50, 0.52, 0.48, 0.50),
        labels,
    )
    decision = ModelSelector(min_auc=0.80, max_brier=0.20).select((useful, irrelevant))
    assert decision.status == "SELECTED"
    assert decision.selected_model_id == "core"
