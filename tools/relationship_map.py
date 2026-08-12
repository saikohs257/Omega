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


def _safe_auc(y: np.ndarray, x: np.ndarray) -> float:
    """AUC with a safe fallback for degenerate target vectors."""
    try:
        return _auc(y, x)
    except (ValueError, IndexError):
        return 0.5


def _directional_gap(a: np.ndarray, b: np.ndarray, relation: str, y: np.ndarray) -> float:
    """Measure temporal order, not operand order.

    The old implementation compared f(a,b) with f(b,a). Every supported
    interaction is effectively commutative at that level, so that quantity was
    identically zero. Here we compare two different temporal hypotheses:

      A -> B : A_t combined with B_{t+1}
      B -> A : B_t combined with A_{t+1}

    The score is evaluated against the common next-state label after trimming
    the final sample. This is a directional temporal diagnostic, not a causal
    proof.
    """
    n = min(len(a), len(b), len(y))
    if n < 3:
        return 0.0
    aa, bb = a[:n], b[:n]
    yy = y[: n - 1]
    ab = interaction_feature(aa[:-1], bb[1:], relation)
    ba = interaction_feature(bb[:-1], aa[1:], relation)
    return _safe_auc(yy, ab) - _safe_auc(yy, ba)


def _lagged_interaction_auc(a: np.ndarray, b: np.ndarray, relation: str, y: np.ndarray) -> float:
    """Score B one step behind A without circular wraparound."""
    n = min(len(a), len(b), len(y))
    if n < 3:
        return 0.5
    return _safe_auc(
        y[1:n],
        interaction_feature(a[1:n], b[: n - 1], relation),
    )


def map_relationships(
    signals: Mapping[str, Iterable[float]],
    labels: Iterable[int],
    *,
    phase: Iterable[float] | None = None,
) -> tuple[RelationshipResult, ...]:
    y = np.asarray(labels, dtype=int)
    arrays = {k: np.asarray(v, dtype=float) for k, v in signals.items()}
    lengths = {len(y), *(len(v) for v in arrays.values())}
    if len(lengths) != 1:
        raise ValueError("signals and labels must have the same length")
    phase_arr = np.asarray(phase, dtype=float) if phase is not None else None
    if phase_arr is not None and len(phase_arr) != len(y):
        raise ValueError("phase must have the same length as labels")

    out: list[RelationshipResult] = []
    for left, right in combinations(arrays, 2):
        a, b = arrays[left], arrays[right]
        la, lb = _safe_auc(y, _normalize(a)), _safe_auc(y, _normalize(b))
        relation, joint = _interaction(a, b, y)
        ji = _safe_auc(y, joint)
        reverse_gap = _directional_gap(a, b, relation, y)
        lag_gain = _lagged_interaction_auc(a, b, relation, y) - ji
        inv_score = _safe_auc(y, interaction_feature(a, -b, relation))
        attenuation_score = _safe_auc(y, interaction_feature(a, 0.5 + 0.5 * b, relation))
        phase_gain = (_phase_auc(y, joint, phase_arr) - ji) if phase_arr is not None else 0.0
        out.append(
            RelationshipResult(
                left,
                right,
                la,
                lb,
                ji,
                ji - max(la, lb),
                reverse_gap,
                lag_gain,
                inv_score - ji,
                attenuation_score - ji,
                phase_gain,
                relation,
            )
        )
    return tuple(sorted(out, key=lambda r: (-r.interaction_gain, -abs(r.reverse_gap), -abs(r.lag_gain))))


def format_report(results: Iterable[RelationshipResult]) -> str:
    rows = ["RELATIONSHIP MAP", "pair | AUC(L) | AUC(R) | interaction | gain | directional_gap | lag_gain | inversion_gain | attenuation_gain | phase_gain | relation"]
    for r in results:
        rows.append(f"{r.left}+{r.right} | {r.left_auc:.4f} | {r.right_auc:.4f} | {r.interaction_auc:.4f} | {r.interaction_gain:.4f} | {r.reverse_gap:.4f} | {r.lag_gain:.4f} | {r.inversion_gain:.4f} | {r.attenuation_gain:.4f} | {r.phase_gain:.4f} | {r.relation}")
    return "\n".join(rows)
