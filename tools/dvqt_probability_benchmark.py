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

def _probabilities(rows: Sequence[TelemetryRow], fields: Sequence[str]):
    buckets: dict[tuple[Any, ...], list[int]] = defaultdict(list)
    pairs = list(zip(rows, rows[1:]))
    for current, nxt in pairs:
        buckets[tuple(getattr(current, f) for f in fields)].append(1 if nxt.mode.value == "EXCITATION" else 0)
    probabilities, labels = [], []
    for current, nxt in pairs:
        outcomes = buckets[tuple(getattr(current, f) for f in fields)]
        if len(outcomes) < 2:
            continue
        y = 1 if nxt.mode.value == "EXCITATION" else 0
        probabilities.append((sum(outcomes) - y) / (len(outcomes) - 1))
        labels.append(y)
    return probabilities, labels

def pr_auc(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    positives = sum(labels)
    if positives == 0:
        return float("nan")
    ordered = sorted(zip(probabilities, labels), key=lambda x: x[0], reverse=True)
    tp = fp = 0
    previous_recall = area = 0.0
    for _, y in ordered:
        if y: tp += 1
        else: fp += 1
        recall = tp / positives
        precision = tp / (tp + fp)
        area += (recall - previous_recall) * precision
        previous_recall = recall
    return area

def benchmark(worlds: Mapping[str, Sequence[TelemetryRow]]) -> dict[str, Any]:
    out = {}
    for name, fields in PROJECTIONS:
        world_metrics = {}
        total_pairs = total_evaluated = 0
        pooled_p, pooled_y = [], []
        for world, rows in worlds.items():
            pairs = max(0, len(rows) - 1)
            p, y = _probabilities(rows, fields)
            total_pairs += pairs; total_evaluated += len(p)
            pooled_p.extend(p); pooled_y.extend(y)
            m = {"evaluated_n": len(p), "coverage": len(p) / max(1, pairs)}
            if len(set(y)) >= 2:
                m.update(brier=brier_score(p,y), log_loss=log_loss(p,y), calibration_error=calibration_error(p,y), auc=binary_auc(p,y), pr_auc=pr_auc(p,y))
            world_metrics[world] = m
        usable = [m for m in world_metrics.values() if "brier" in m]
        pr = [m["pr_auc"] for m in usable if isfinite(m["pr_auc"])]
        pooled = {}
        if len(set(pooled_y)) >= 2:
            pooled = {"brier":brier_score(pooled_p,pooled_y), "log_loss":log_loss(pooled_p,pooled_y), "calibration_error":calibration_error(pooled_p,pooled_y), "auc":binary_auc(pooled_p,pooled_y), "pr_auc":pr_auc(pooled_p,pooled_y)}
        out[name] = {"dimensions":len(fields), "coverage":total_evaluated/max(1,total_pairs), "brier":sum(m["brier"] for m in usable)/len(usable) if usable else float("nan"), "log_loss":sum(m["log_loss"] for m in usable)/len(usable) if usable else float("nan"), "calibration_error":sum(m["calibration_error"] for m in usable)/len(usable) if usable else float("nan"), "auc":sum(m["auc"] for m in usable)/len(usable) if usable else float("nan"), "pr_auc":sum(pr)/len(pr) if pr else float("nan"), "pooled":pooled, "worlds":world_metrics}
    return out
