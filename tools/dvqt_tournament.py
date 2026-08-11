from __future__ import annotations

from typing import Any, Mapping, Sequence

from tools.dvqt_probability_benchmark import benchmark

ORDER = ("brier", "log_loss", "calibration_error", "auc", "pr_auc", "coverage", "dimensions")
LOWER = {"brier", "log_loss", "calibration_error", "dimensions"}


def rank(report: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for name, m in report.items():
        rows.append({"name": name, **{k: m.get(k) for k in ORDER}})
    # Lexicographic scoreboard: predictive metrics first, then coverage, then complexity.
    def key(row):
        values = []
        for metric in ORDER:
            value = row[metric]
            if value is None or value != value:
                value = float("inf") if metric in LOWER else float("-inf")
            values.append(value if metric in LOWER else -value)
        return tuple(values)
    return sorted(rows, key=key)


def tournament(worlds: Mapping[str, Sequence[Any]]) -> dict[str, Any]:
    report = benchmark(worlds)
    ranked = rank(report)
    return {"scoreboard_order": ORDER, "ranking": ranked, "metrics": report}
