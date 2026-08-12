from runtime.contracts import ProbabilityContract
from runtime.controls import prepare_controls_run
from runtime.selection import SelectionThresholds
from tiamat.model_selection import CandidateSpec, ModelSelector, evaluate_candidate


def test_controls_run_excludes_incomparable_predictors_without_aborting() -> None:
    run = prepare_controls_run(
        {
            "good": (0.1, 0.9, 0.2, 0.8),
            "bad": (0.1, 1.2, 0.2, 0.8),
        }
    )

    assert tuple(run.comparable_predictions) == ("good",)
    assert run.incomparable_predictions == ("bad",)
    assert run.partition.reason_for("bad") is not None


def test_controls_run_uses_custom_probability_contract() -> None:
    contract = ProbabilityContract(minimum=0.05, maximum=0.95)
    run = prepare_controls_run(
        {"inside": (0.05, 0.95), "outside": (0.0, 0.9)},
        contract=contract,
    )

    assert run.partition.valid == ("inside",)
    assert run.incomparable_predictions == ("outside",)


def test_controls_candidates_can_be_scored_only_after_preflight() -> None:
    probabilities = {
        "valid": (0.05, 0.95, 0.05, 0.95),
        "invalid": (0.05, 1.10, 0.05, 0.95),
        "weak": (0.49, 0.51, 0.49, 0.51),
    }
    run = prepare_controls_run(probabilities)
    labels = (0, 1, 0, 1)

    metrics = tuple(
        evaluate_candidate(CandidateSpec(model_id=model_id, features=("control",)), values, labels)
        for model_id, values in run.comparable_predictions.items()
    )
    decision = ModelSelector(selection_thresholds=SelectionThresholds()).select(metrics)

    assert "invalid" not in run.partition.valid
    assert "valid" in run.partition.valid
    assert decision.status == "SELECTED"
    assert decision.selected_model_id == "valid"
