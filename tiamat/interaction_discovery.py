"""Blind interaction discovery over a collection of raw signals.

The detector deliberately knows nothing about which signals generated the labels.
It searches individual signals, pairwise interaction transforms, and permutation
controls, then promotes a pair only when its interaction advantage survives the
controls.  This is a research/diagnostic module, not a production predictor.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping

import numpy as np


@dataclass(frozen=True)
class InteractionResult:
    left: str
    right: str
    individual_auc_left: float
    individual_auc_right: float
    joint_auc: float
    synergy: float
    shuffled_auc_mean: float
    shuffle_gap: float
    relation: str
    promoted: bool


def _auc(y: np.ndarray, score: np.ndarray) -> float:
    """Compute ROC AUC with sklearn-compatible tie handling using NumPy only."""
    y = np.asarray(y, dtype=int)
    score = np.asarray(score, dtype=float)
    positives = y == 1
    negatives = y == 0
    n_pos = int(positives.sum())
    n_neg = int(negatives.sum())
    if n_pos == 0 or n_neg == 0:
        return 0.5

    # Average ranks for ties; equivalent to the Mann-Whitney formulation of AUC.
    order = np.argsort(score, kind="mergesort")
    sorted_scores = score[order]
    ranks = np.empty(score.size, dtype=float)
    start = 0
    while start < score.size:
        end = start + 1
        while end < score.size and sorted_scores[end] == sorted_scores[start]:
            end += 1
        ranks[order[start:end]] = (start + 1 + end) / 2.0
        start = end

    positive_rank_sum = float(ranks[positives].sum())
    return (positive_rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def _normalize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    lo, hi = np.nanmin(x), np.nanmax(x)
    if hi == lo:
        return np.zeros_like(x)
    return (x - lo) / (hi - lo)


def interaction_feature(a: np.ndarray, b: np.ndarray, relation: str) -> np.ndarray:
    """Construct a relationship feature without using labels."""
    a = _normalize(a)
    b = _normalize(b)
    if relation == "and":
        return a * b
    if relation == "xor":
        return np.abs(a - b)
    if relation == "threshold":
        return ((a > 0.5) & (b > 0.5)).astype(float)
    if relation == "conditional":
        return a * b
    if relation == "multiplicative":
        return a * b
    raise ValueError(f"unknown relation: {relation}")


def infer_relation(a: np.ndarray, b: np.ndarray, y: np.ndarray) -> str:
    candidates = ("and", "xor", "threshold", "conditional", "multiplicative")
    scores = {r: _auc(y, interaction_feature(a, b, r)) for r in candidates}
    return max(scores, key=scores.get)


def discover_interactions(
    signals: Mapping[str, Iterable[float]],
    labels: Iterable[int],
    *,
    shuffle_trials: int = 8,
    min_synergy: float = 0.10,
    min_shuffle_gap: float = 0.10,
) -> tuple[InteractionResult, ...]:
    """Blindly scan signal pairs and return only control-surviving interactions."""
    y = np.asarray(labels, dtype=int)
    arrays = {k: np.asarray(v, dtype=float) for k, v in signals.items()}
    individual = {k: _auc(y, _normalize(v)) for k, v in arrays.items()}
    results: list[InteractionResult] = []
    rng = np.random.default_rng(20260811)

    for left, right in combinations(arrays, 2):
        a, b = arrays[left], arrays[right]
        relation = infer_relation(a, b, y)
        joint = interaction_feature(a, b, relation)
        joint_auc = _auc(y, joint)
        synergy = joint_auc - max(individual[left], individual[right])

        shuffled = []
        for _ in range(shuffle_trials):
            shuffled_b = rng.permutation(b)
            shuffled_relation = interaction_feature(a, shuffled_b, relation)
            shuffled.append(_auc(y, shuffled_relation))
        shuffled_mean = float(np.mean(shuffled))
        shuffle_gap = joint_auc - shuffled_mean
        promoted = synergy >= min_synergy and shuffle_gap >= min_shuffle_gap
        results.append(
            InteractionResult(
                left, right, individual[left], individual[right], joint_auc,
                synergy, shuffled_mean, shuffle_gap, relation, promoted,
            )
        )
    return tuple(sorted(results, key=lambda r: (not r.promoted, -r.synergy, -r.shuffle_gap)))


def format_report(results: Iterable[InteractionResult]) -> str:
    rows = [
        "INTERACTION DISCOVERY",
        "pair | AUC(left) | AUC(right) | joint AUC | synergy | shuffled AUC | shuffle gap | relation | promoted",
    ]
    for r in results:
        rows.append(
            f"{r.left}+{r.right} | {r.individual_auc_left:.6f} | {r.individual_auc_right:.6f} | "
            f"{r.joint_auc:.6f} | {r.synergy:.6f} | {r.shuffled_auc_mean:.6f} | "
            f"{r.shuffle_gap:.6f} | {r.relation} | {r.promoted}"
        )
    return "\n".join(rows)
