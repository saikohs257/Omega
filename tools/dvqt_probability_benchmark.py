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


def _label(row: TelemetryRow) -> int:
    target = row.extras.get("target")
    if target is not None:
        return int(bool(target))
    return int(row.mode.value == "E")


def _key(row: TelemetryRow, fields: Sequence[str]) -> tuple[Any, ...]:
    return tuple(getattr(row, f) for f in fields)


def _probabilities(rows: Sequence[TelemetryRow], fields: Sequence[str]) -> tuple[list[float], list[int]]:
    """Chronological leave-one-out empirical probabilities within state buckets.

    The canonical corpus intentionally uses repeated levels.  Sparse buckets are
    still useful evidence, but singleton buckets cannot support an empirical
    leave-one-out probability.  Those rows are omitted rather than poisoning the
    whole projection with NaNs.
    """
    buckets: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    pairs = list(zip(rows, rows[1:]))
    for current, nxt in pairs:
        buckets[_key(current, fields)].append(_label(nxt))

    probabilities: list[float] = []
    labels: list[int] = []
    for current, nxt in pairs:
        outcomes = buckets[_key(current, fields)]
        if len(outcomes) < 2:
            continue
        y = _label(nxt)
        probabilities.append((sum(outcomes) - y) / (len(outcomes) - 1))
        labels.append(y)
    return probabilities, labels


def pr_auc(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    positives = sum(labels)
    if positives == 0 or not labels:
        return float("nan")
    ordered = sorted(zip(probabilities, labels), key=lambda x: x[0], reverse=True)
    tp = fp = 0
    previous_recall = area = 0.0
    for _, y in ordered:
        if y:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / (tp + fp)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area


def _metrics(probabilities: Sequence[float], labels: Sequence[int]) -> dict[str, float] | None:
    if len(labels) < 2 or len(set(labels)) < 2:
        return None
    return {
        "brier": brier_score(probabilities, labels),
        "log_loss": log_loss(probabilities, labels),
        "calibration_error": calibration_error(probabilities, labels),
        "auc": binary_auc(probabilities, labels),
        "pr_auc": pr_auc(probabilities, labels),
    }


def benchmark(worlds: Mapping[str, Sequence[TelemetryRow]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, fields in PROJECTIONS:
        world_metrics: dict[str, Any] = {}
        total_pairs = total_evaluated = 0
        pooled_p: list[float] = []
        pooled_y: list[int] = []

        for world, rows in worlds.items():
            pairs = max(0, len(rows) - 1)
            p, y = _probabilities(rows, fields)
            total_pairs += pairs
            total_evaluated += len(p)
            pooled_p.extend(p)
            pooled_y.extend(y)
            metrics = _metrics(p, y)
            m: dict[str, Any] = {
                "evaluated_n": len(p),
                "coverage": len(p) / max(1, pairs),
            }
            if metrics is not None:
                m.update(metrics)
            world_metrics[world] = m

        usable = [m for m in world_metrics.values() if "brier" in m]
        pooled_metrics = _metrics(pooled_p, pooled_y) or {}
        finite_pr = [m["pr_auc"] for m in usable if isfinite(m["pr_auc"])]

        out[name] = {
            "dimensions": len(fields),
            "coverage": total_evaluated / max(1, total_pairs),
            "brier": sum(m["brier"] for m in usable) / len(usable) if usable else float("nan"),
            "log_loss": sum(m["log_loss"] for m in usable) / len(usable) if usable else float("nan"),
            "calibration_error": sum(m["calibration_error"] for m in usable) / len(usable) if usable else float("nan"),
            "auc": sum(m["auc"] for m in usable) / len(usable) if usable else float("nan"),
            "pr_auc": sum(finite_pr) / len(finite_pr) if finite_pr else float("nan"),
            "pooled": pooled_metrics,
            "worlds": world_metrics,
        }
    return out
