from tools.dvqt_tournament import rank


def test_rank_prefers_predictive_score_before_complexity():
    report = {
        "small": {"brier": .10, "log_loss": .20, "calibration_error": .05, "auc": .90, "pr_auc": .80, "coverage": .90, "dimensions": 3},
        "large": {"brier": .11, "log_loss": .21, "calibration_error": .06, "auc": .91, "pr_auc": .81, "coverage": .99, "dimensions": 5},
    }
    assert rank(report)[0]["name"] == "small"


def test_complexity_breaks_exact_tie():
    base = {"brier": .10, "log_loss": .20, "calibration_error": .05, "auc": .90, "pr_auc": .80, "coverage": .90}
    report = {"small": {**base, "dimensions": 3}, "large": {**base, "dimensions": 5}}
    assert rank(report)[0]["name"] == "small"
