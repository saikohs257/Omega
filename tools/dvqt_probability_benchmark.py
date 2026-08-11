from __future__ import annotations

from collections import defaultdict
from math import isfinite
from typing import Any, Mapping, Sequence

from tiamat.model_selection import binary_auc, brier_score, calibration_error, log_loss
from tiamat.telemetry import TelemetryRow


PROJECTIONS = (
    ("DVQT", ("D", "V", "mode", "tau_mode")),
    ("DVQT+B", ("D", "V", "mode", "tau_mode", "B")),
    ("DVQ+B", ("D", "V", "mode", "B")),
    ("DV+B", ("D", "V", "B")),
)


def _probabilities(rows: Sequence[TelemetryRow], fields: Sequence[str]) -> tuple[list[float], list[int], int]:
    buckets: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    pairs = list(zip(rows, rows[1:]))
    for current, nxt in pairs:
        key = tuple(getattr(current, f) for f in fields)
        buckets[key].append(1 if nxt.mode.value == "EXCITATION" else 0)

    probabilities: list[float] = []
    labels: list[int] = []
    for current, nxt in pairs:
        key = tuple(getattr(current, f) for f in fields)
        outcomes = buckets[key]
        n = len(outcomes)
        if n < 2:
            continue
        y = 1 if nxt.mode.value == "EXCITATION" else 0
        p = (sum(outcomes) - y) / (n - 1)
        probabilities.append(p)
        labels.append(y)
    return probabilities, labels, len(probabilities)


def pr_auc(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    positives = sum(labels)
    if positives == 0:
        return float("nan")
    ordered = sorted(zip(probabilities, labels), key=lambda x: x[0], reverse=True)
    tp = fp = 0
    prev_recall = 0.0
    area = 0.0
    for p, y in ordered:
        if y:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / (tp + fp)
        area += (recall - prev_recall) * precision
        prev_recall = recall
    return area


def benchmark(worlds: Mapping[str, Sequence[TelemetryRow]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, fields in PROJECTIONS:
        world_metrics: dict[str, Any] = {}
        for world, rows in worlds.items():
            probabilities, labels, evaluated_n = _probabilities(rows, fields)
            if len(set(labels)) < 2:
                world_metrics[world] = {"evaluated_n": evaluated_n}
                continue
            world_metrics[world] = {
                "evaluated_n": evaluated_n,
                "coverage": evaluated_n / max(1, len(rows) - 1),
                "brier": brier_score(probabilities, labels),
                "log_loss": log_loss(probabilities, labels),
                "calibration_error": calibration_error(probabilities, labels),
                "auc": binary_auc(probabilities, labels),
                "pr_auc": pr_auc(probabilities, labels),
            }

        usable = [m for m in world_metrics.values() if "brier" in m]
        out[name] = {
            "dimensions": len(fields),
            "coverage": sum(m["coverage"] for m in usable) / len(usable) if usable else float("nan"),
            "brier": sum(m["brier"] for m in usable) / len(usable) if usable else float("nan"),
            "log_loss": sum(m["log_loss"] for m in usable) / len(usable) if usable else float("nan"),
            "calibration_error": sum(m["calibration_error"] for m in usable) / len(usable) if usable else float("nan"),
            "auc": sum(m["auc"] for m in usable) / len(usable) if usable else float("nan"),
            "pr_auc": sum(m["pr_auc"] for m in usable if isfinite(m["pr_auc"])) / max(1, sum(isfinite(m["pr_auc"]) for m in usable)),
            "worlds": world_metrics,
        }
    return out
