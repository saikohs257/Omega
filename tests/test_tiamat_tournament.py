from __future__ import annotations

from tiamat.candidate_library import DEFAULT_CANDIDATE_MODELS
from tiamat.model_selection import ModelSelector
from tiamat.tournament import TournamentCase, TournamentRunner


def test_tournament_selects_strongest_frontier_candidate() -> None:
    labels = (0, 0, 0, 1, 1, 1)
    predictions = {
        "M_D": (0.35, 0.40, 0.45, 0.55, 0.60, 0.65),
        "M_DV": (0.10, 0.15, 0.20, 0.80, 0.85, 0.90),
        "M_DQV": (0.02, 0.05, 0.10, 0.90, 0.95, 0.98),
        "M_DQRV": (0.04, 0.06, 0.08, 0.88, 0.92, 0.96),
        "M_DQVF": (0.12, 0.15, 0.18, 0.76, 0.82, 0.88),
        "M_DQVPATH": (0.14, 0.18, 0.21, 0.74, 0.79, 0.84),
        "M_DQVCPL": (0.14, 0.17, 0.20, 0.76, 0.81, 0.86),
        "M_FULL_CONTEXT": (0.25, 0.25, 0.25, 0.75, 0.75, 0.75),
    }
    case = TournamentCase(name="causal-world", labels=labels, heldout_predictions=predictions, max_size=4)
    runner = TournamentRunner(selector=ModelSelector(min_auc=0.80, max_brier=0.20), specs=DEFAULT_CANDIDATE_MODELS)

    result = runner.run_case(case)

    assert result.report.best is not None
    assert result.report.best.spec.model_id == "M_DQV"
    assert result.decision.status == "SELECTED"
    assert result.decision.selected_model_id == "M_DQV"
    assert "M_FULL_CONTEXT" in result.report.rejected


def test_tournament_can_remain_unresolved_when_evidence_is_weak() -> None:
    labels = (0, 0, 0, 1, 1, 1)
    predictions = {
        "M_D": (0.49, 0.50, 0.51, 0.50, 0.49, 0.50),
        "M_DV": (0.48, 0.49, 0.50, 0.51, 0.50, 0.49),
        "M_DQV": (0.47, 0.48, 0.49, 0.50, 0.51, 0.52),
    }
    case = TournamentCase(name="weak-world", labels=labels, heldout_predictions=predictions, max_size=3)
    runner = TournamentRunner(selector=ModelSelector(min_auc=0.80, max_brier=0.20), specs=DEFAULT_CANDIDATE_MODELS)

    result = runner.run_case(case)

    assert result.decision.status == "UNRESOLVED"
    assert result.decision.selected_model_id is None
