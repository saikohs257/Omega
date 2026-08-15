from __future__ import annotations

from dataclasses import dataclass
from math import log
from typing import Iterable


@dataclass(frozen=True, slots=True)
class PredictionRow:
    index: int
    probability: float
    outcome: bool


@dataclass(frozen=True, slots=True)
class Evaluation:
    n: int
    brier: float
    log_loss: float
    positives: int
    predicted_positive: int
    true_positive: int
    false_positive: int
    false_negative: int


def evaluate_binary(rows: Iterable[PredictionRow], threshold: float = 0.5) -> Evaluation:
    data = list(rows)
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must lie in [0, 1]")
    if not data:
        raise ValueError("at least one prediction is required")
    brier = 0.0
    log_loss = 0.0
    tp = fp = fn = 0
    positives = predicted_positive = 0
    for row in data:
        p = min(1.0 - 1e-12, max(1e-12, float(row.probability)))
        y = bool(row.outcome)
        brier += (p - float(y)) ** 2
        log_loss -= log(p if y else 1.0 - p)
        pred = p >= threshold
        positives += int(y)
        predicted_positive += int(pred)
        tp += int(pred and y)
        fp += int(pred and not y)
        fn += int((not pred) and y)
    n = len(data)
    return Evaluation(n, brier / n, log_loss / n, positives, predicted_positive, tp, fp, fn)


def first_lead_time(rows: Iterable[PredictionRow], threshold: float = 0.5) -> int | None:
    """Return the earliest index at/above threshold before a positive outcome."""
    data = sorted(rows, key=lambda row: row.index)
    positives = {row.index for row in data if row.outcome}
    if not positives:
        return None
    target = min(positives)
    candidates = [row.index for row in data if row.index < target and row.probability >= threshold]
    return None if not candidates else target - min(candidates)
