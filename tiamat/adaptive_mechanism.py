"""Adaptive, online mechanism selection for world-agnostic experiments.

The adaptive selector uses a cheap prior only to order probes, then validates
candidates on past observations whose outcomes are already known. Current or
held-out observations never influence selection.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from .world_selector import rank_candidates


@dataclass(frozen=True, slots=True)
class ProbeResult:
    component: str
    brier: float
    log_loss: float
    compatibility: float
    probe_index: int


@dataclass(frozen=True, slots=True)
class AdaptiveDecision:
    selected: tuple[str, ...]
    probes: tuple[ProbeResult, ...]
    abstained: bool
    stopped_early: bool


def _brier(labels: Sequence[int], predictions: Sequence[float]) -> float:
    return sum((float(y) - p) ** 2 for y, p in zip(labels, predictions)) / len(labels)


def _log_loss(labels: Sequence[int], predictions: Sequence[float]) -> float:
    eps = 1e-12
    return -sum(
        y * math.log(max(eps, p)) + (1 - y) * math.log(max(eps, 1 - p))
        for y, p in zip(labels, predictions)
    ) / len(labels)


def discover(
    mechanisms: frozenset[str],
    labels: Sequence[int],
    predictions: Mapping[str, Sequence[float]],
    *,
    feedback_n: int,
    budget: int = 3,
    margin: float = 0.02,
) -> AdaptiveDecision:
    """Select mechanisms from historical feedback and stop when decisive."""
    if feedback_n <= 0 or feedback_n > len(labels):
        raise ValueError("feedback_n must be within the observed history")
    ranked = rank_candidates(mechanisms)
    if not ranked:
        return AdaptiveDecision((), (), True, False)

    eligible = ranked[: max(1, budget)]
    probes: list[ProbeResult] = []
    for idx, candidate in enumerate(eligible, start=1):
        stream = predictions.get(candidate.component)
        if stream is None or len(stream) < feedback_n:
            continue
        probes.append(
            ProbeResult(
                candidate.component,
                _brier(labels[:feedback_n], stream[:feedback_n]),
                _log_loss(labels[:feedback_n], stream[:feedback_n]),
                candidate.compatibility,
                idx,
            )
        )
        ordered = sorted(probes, key=lambda x: (x.brier, x.log_loss, -x.compatibility, x.component))
        if len(ordered) >= 2 and ordered[1].brier - ordered[0].brier >= margin:
            return AdaptiveDecision((ordered[0].component,), tuple(probes), False, True)

    if not probes:
        return AdaptiveDecision((), (), True, False)
    ordered = sorted(probes, key=lambda x: (x.brier, x.log_loss, -x.compatibility, x.component))
    best = ordered[0]
    ties = tuple(
        x.component for x in ordered
        if abs(x.brier - best.brier) <= 1e-9 and abs(x.log_loss - best.log_loss) <= 1e-9
    )
    return AdaptiveDecision(ties, tuple(probes), False, False)
