"""CLI scorecard for the mechanism-selector laboratory."""
from __future__ import annotations

from .expanded_world_selector_eval import aggregate, evaluate_world
from .expanded_worlds import build_expanded_worlds


def main() -> None:
    worlds = build_expanded_worlds()
    print("TIAMAT EXPANDED SELECTOR SCORECARD")
    stats = aggregate(worlds, k=3)
    for key, value in stats.items():
        print(f"{key}={value:.6f}")
    print("WORLD RESULTS")
    for world in worlds:
        result = evaluate_world(world, k=3)
        print(
            f"WORLD {world.name} "
            f"known={result['known']} "
            f"abstain={result['abstained']} "
            f"top1={result['top1'] or '-'} "
            f"topk={','.join(result['topk']) or '-'} "
            f"empirical={','.join(result['winners']) or '-'} "
            f"top1_hit={result['top1_hit']} "
            f"topk_hit={result['topk_hit']} "
            f"ambiguous={result['ambiguous']}"
        )


if __name__ == "__main__":
    main()
