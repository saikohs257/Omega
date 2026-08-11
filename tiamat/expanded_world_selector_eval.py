"""Evaluation of world-conditioned selector priors against empirical evidence.

The selector is intentionally treated as a hypothesis generator. This module
measures whether its top candidate set contains the empirically strongest
candidate, whether multiple candidates are tied/equivalent, and whether the
selector correctly abstains when no mechanism is known.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from .expanded_worlds import ExpandedWorld, build_expanded_worlds
from .world_selector import rank_candidates


@dataclass(frozen=True, slots=True)
class EmpiricalMetric:
    component: str
    brier: float
    log_loss: float
    auc: float


def brier(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    return sum((float(label) - prob) ** 2 for label, prob in zip(y, p)) / len(y)


def log_loss(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    eps = 1e-12
    return -sum(
        label * math.log(max(eps, prob)) + (1 - label) * math.log(max(eps, 1 - prob))
        for label, prob in zip(y, p)
    ) / len(y)


def auc(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    pos = [x for x, label in zip(p, y) if label == 1]
    neg = [x for x, label in zip(p, y) if label == 0]
    if not pos or not neg:
        return 0.5
    wins = sum(1.0 if a > b else 0.5 if a == b else 0.0 for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def empirical_metrics(world: ExpandedWorld) -> tuple[EmpiricalMetric, ...]:
    rows = []
    for component, predictions in world.predictions.items():
        rows.append(EmpiricalMetric(component, brier(world.labels, predictions), log_loss(world.labels, predictions), auc(world.labels, predictions)))
    return tuple(rows)


def best_components(metrics: tuple[EmpiricalMetric, ...], tol: float = 1e-9) -> tuple[str, ...]:
    if not metrics:
        return ()
    ordered = sorted(metrics, key=lambda m: (m.brier, m.log_loss, -m.auc, m.component))
    best = ordered[0]
    return tuple(m.component for m in ordered if abs(m.brier - best.brier) <= tol and abs(m.log_loss - best.log_loss) <= tol and abs(m.auc - best.auc) <= tol)


def selector_topk(world: ExpandedWorld, k: int = 3) -> tuple[str, ...]:
    return tuple(item.component for item in rank_candidates(world.mechanisms, limit=k))


def evaluate_world(world: ExpandedWorld, *, k: int = 3) -> dict[str, object]:
    ranked = rank_candidates(world.mechanisms)
    topk = tuple(item.component for item in ranked[:k])
    metrics = empirical_metrics(world)
    winners = best_components(metrics)
    known = "unknown" not in world.mechanisms
    return {
        "known": known,
        "abstained": not ranked,
        "top1": ranked[0].component if ranked else None,
        "topk": topk,
        "winners": winners,
        "top1_hit": bool(ranked) and bool(set((ranked[0].component,)) & set(winners)),
        "topk_hit": bool(set(topk) & set(winners)),
        "ambiguous": len(winners) > 1,
    }


def aggregate(worlds: tuple[ExpandedWorld, ...], *, k: int = 3) -> dict[str, float]:
    rows = [evaluate_world(world, k=k) for world in worlds]
    known = [r for r in rows if r["known"]]
    unknown = [r for r in rows if not r["known"]]
    return {
        "worlds": float(len(rows)),
        "known_worlds": float(len(known)),
        "unknown_worlds": float(len(unknown)),
        "top1_hit_rate": sum(bool(r["top1_hit"]) for r in known) / len(known) if known else 0.0,
        "topk_hit_rate": sum(bool(r["topk_hit"]) for r in known) / len(known) if known else 0.0,
        "ambiguity_rate": sum(bool(r["ambiguous"]) for r in known) / len(known) if known else 0.0,
        "known_abstention_rate": sum(bool(r["abstained"]) for r in known) / len(known) if known else 0.0,
        "unknown_abstention_rate": sum(bool(r["abstained"]) for r in unknown) / len(unknown) if unknown else 0.0,
    }


def main() -> None:
    worlds = build_expanded_worlds()
    print("TIAMAT EXPANDED SELECTOR EVALUATION")
    stats = aggregate(worlds, k=3)
    for key, value in stats.items():
        print(f"{key}={value:.6f}" if isinstance(value, float) else f"{key}={value}")
    print("WORLD RESULTS")
    for world in worlds:
        result = evaluate_world(world, k=3)
        print(
            f"WORLD {world.name} known={result['known']} abstain={result['abstained']} "
            f"top1={result['top1'] or '-'} topk={','.join(result['topk']) or '-'} "
            f"winner={','.join(result['winners']) or '-'} "
            f"top1_hit={result['top1_hit']} topk_hit={result['topk_hit']} "
            f"ambiguous={result['ambiguous']}"
        )


if __name__ == "__main__":
    main()
