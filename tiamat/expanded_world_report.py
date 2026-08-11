"""CLI report for the expanded generic synthetic-world laboratory."""
from __future__ import annotations

import math

from .expanded_worlds import build_expanded_worlds
from .world_selector import rank_candidates


def auc(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    pos = [x for x, label in zip(p, y) if label == 1]
    neg = [x for x, label in zip(p, y) if label == 0]
    if not pos or not neg:
        return 0.5
    wins = sum(1.0 if a > b else 0.5 if a == b else 0.0 for a in pos for b in neg)
    return wins / (len(pos) * len(neg))


def brier(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    return sum((float(label) - prob) ** 2 for label, prob in zip(y, p)) / len(y)


def log_loss(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    eps = 1e-12
    return -sum(
        label * math.log(max(eps, prob)) + (1 - label) * math.log(max(eps, 1 - prob))
        for label, prob in zip(y, p)
    ) / len(y)


def calibration_error(y: tuple[int, ...], p: tuple[float, ...]) -> float:
    return abs(sum(p) / len(p) - sum(y) / len(y))


def main() -> None:
    worlds = build_expanded_worlds()
    print("TIAMAT EXPANDED WORLD LAB")
    print(f"worlds={len(worlds)}")
    for world in worlds:
        print(f"WORLD {world.name} truth={world.truth or 'none'} mechanisms={','.join(sorted(world.mechanisms))}")
        ranked = rank_candidates(world.mechanisms, limit=6)
        print("  SELECTOR " + ", ".join(f"{item.component}:{item.compatibility:.1f}" for item in ranked))
        for candidate, predictions in world.predictions.items():
            print(
                f"  {candidate}: auc={auc(world.labels, predictions):.6f} "
                f"brier={brier(world.labels, predictions):.6f} "
                f"log_loss={log_loss(world.labels, predictions):.6f} "
                f"calibration_error={calibration_error(world.labels, predictions):.6f}"
            )


if __name__ == "__main__":
    main()
