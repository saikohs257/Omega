from tools.dvqt_canonical_corpus import canonical_worlds
from tools.dvqt_probability_benchmark import benchmark


def test_canonical_benchmark_has_usable_metrics_and_coverage():
    report = benchmark(canonical_worlds())
    assert report
    for name, metrics in report.items():
        assert metrics["coverage"] > 0
        assert metrics["pooled"]
        assert metrics["brier"] == metrics["brier"]
        assert metrics["log_loss"] == metrics["log_loss"]
        assert metrics["auc"] == metrics["auc"]
        assert metrics["pr_auc"] == metrics["pr_auc"]
