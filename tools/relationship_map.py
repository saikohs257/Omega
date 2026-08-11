"""Measure pair relationships, temporal directionality, lag, and regime sensitivity."""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping

import numpy as np

from tiamat.interaction_discovery import _auc, _normalize, interaction_feature


@dataclass(frozen=True)
class RelationshipResult:
    left: str
    right: str
    left_auc: float
    right_auc: float
    interaction_auc: float
    interaction_gain: float
    reverse_gap: float
    lag_gain: float
    inversion_gain: float
    attenuation_gain: float
    phase_gain: float
    relation: str


def _phase_auc(y: np.ndarray, x: np.ndarray, phase: np.ndarray) -> float:
    mask = phase > np.median(phase)
    if mask.all() or (~mask).all():
        return _auc(y, x)
    scores = x.copy()
    scores[~mask] *= 0.5
    return _auc(y, scores)


def _interaction(a: np.ndarray, b: np.ndarray, y: np.ndarray) -> tuple[str, np.ndarray]:
    candidates = ("and", "xor", "threshold", "conditional", "multiplicative")
    scores = {r: _auc(y, interaction_feature(a, b, r)) for r in candidates}
    relation = max(scores, key=scores.get)
    return relation, interaction_feature(a, b, relation)


def _directional_gap(a: np.ndarray, b: np.ndarray, relation: str, y: np.ndarray) -> float:
    """Measure temporal ordering, not commutative operand ordering.

    Positive means a(t) with b(t+1) predicts y better than b(t) with a(t+1).
    """
    if len(a) < 3 or len(a) != len(b) or len(y) != len(a):
        return 0.0
    a_t, b_t = a[:-1], b[:-1]
    a_next, b_next = a[1:], b[1:]
    forward = interaction_feature(a_t, b_next, relation)
    reverse = interaction_feature(b_t, a_next, relation)
    return float(_auc(y[1:], forward) - _auc(y[1:], reverse))


def map_relationships(signals: Mapping[str, Iterable[float]], labels: Iterable[int], *, phase: Iterable[float] | None = None) -> tuple[RelationshipResult, ...]:
    y = np.asarray(labels, dtype=int)
    arrays = {k: np.asarray(v, dtype=float) for k, v in signals.items()}
    phase_arr = np.asarray(phase, dtype=float) if phase is not None else None
    out: list[RelationshipResult] = []
    for left, right in combinations(arrays, 2):
        a, b = arrays[left], arrays[right]
        la, lb = _auc(y, _normalize(a)), _auc(y, _normalize(b))
        relation, joint = _interaction(a, b, y)
        ji = _auc(y, joint)
        directional = _directional_gap(a, b, relation, y)
        lag = np.roll(b, 1)
        lag_gain = _auc(y, interaction_feature(a, lag, relation)) - ji
        inv_score = _auc(y, interaction_feature(a, -b, relation))
        attenuation_score = _auc(y, interaction_feature(a, 0.5 + 0.5 * b, relation))
        phase_gain = (_phase_auc(y, joint, phase_arr) - ji) if phase_arr is not None else 0.0
        out.append(RelationshipResult(left, right, la, lb, ji, ji - max(la, lb), directional, lag_gain, inv_score - ji, attenuation_score - ji, phase_gain, relation))
    return tuple(sorted(out, key=lambda r: (-r.interaction_gain, -abs(r.reverse_gap), -abs(r.lag_gain))))


def format_report(results: Iterable[RelationshipResult]) -> str:
    rows = ["RELATIONSHIP MAP", "pair | AUC(L) | AUC(R) | interaction | gain | directional_gap | lag_gain | inversion_gain | attenuation_gain | phase_gain | relation"]
    for r in results:
        rows.append(f"{r.left}+{r.right} | {r.left_auc:.4f} | {r.right_auc:.4f} | {r.interaction_auc:.4f} | {r.interaction_gain:.4f} | {r.reverse_gap:.4f} | {r.lag_gain:.4f} | {r.inversion_gain:.4f} | {r.attenuation_gain:.4f} | {r.phase_gain:.4f} | {r.relation}")
    return "\n".join(rows)
