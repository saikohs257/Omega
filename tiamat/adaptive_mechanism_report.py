"""Benchmark adaptive online selection against the static dictionary prior."""
from __future__ import annotations

from .adaptive_mechanism import discover
from .expanded_worlds import build_expanded_worlds
from .expanded_world_selector_eval import best_components
from .world_selector import rank_candidates


def _heldout_metrics(world, components, start: int):
    rows = []
    y = world.labels[start:]
    for component in components:
        p = world.predictions[component][start:]
        brier = sum((float(a) - b) ** 2 for a, b in zip(y, p)) / len(y)
        rows.append((component, brier))
    return tuple(sorted(rows, key=lambda x: (x[1], x[0])))


def main() -> None:
    worlds = build_expanded_worlds()
    known = [w for w in worlds if "unknown" not in w.mechanisms]
    feedback_n = len(worlds[0].labels) // 2
    adaptive_hits = 0
    static_hits = 0
    probe_total = 0
    early = 0
    abstain = 0
    print("TIAMAT ADAPTIVE MECHANISM DISCOVERY")
    print("SELECTION_BOUNDARY", feedback_n)
    for world in worlds:
        if "unknown" in world.mechanisms:
            decision = discover(world.mechanisms, world.labels, world.predictions, feedback_n=feedback_n)
            abstain += int(decision.abstained)
            print(f"WORLD {world.name} adaptive=ABSTAIN probes=0")
            continue
        decision = discover(world.mechanisms, world.labels, world.predictions, feedback_n=feedback_n)
        heldout = _heldout_metrics(world, tuple(world.predictions), feedback_n)
        winner_brier = heldout[0][1]
        winners = tuple(name for name, score in heldout if abs(score - winner_brier) <= 1e-9)
        adaptive_hit = bool(set(decision.selected) & set(winners))
        ranked = rank_candidates(world.mechanisms)
        static_top = ranked[0].component if ranked else None
        static_hit = static_top in winners
        adaptive_hits += int(adaptive_hit)
        static_hits += int(static_hit)
        probe_total += len(decision.probes)
        early += int(decision.stopped_early)
        print(
            f"WORLD {world.name} adaptive={','.join(decision.selected) or '-'} "
            f"static={static_top or '-'} winner={','.join(winners)} "
            f"adaptive_hit={adaptive_hit} static_hit={static_hit} "
            f"probes={len(decision.probes)} early={decision.stopped_early}"
        )
    n = len(known)
    print(f"known_worlds={n}")
    print(f"adaptive_topk_hit_rate={adaptive_hits / n:.6f}")
    print(f"static_top1_hit_rate={static_hits / n:.6f}")
    print(f"adaptive_avg_probes={probe_total / n:.6f}")
    print(f"adaptive_early_stop_rate={early / n:.6f}")
    print(f"unknown_abstentions={abstain}")


if __name__ == "__main__":
    main()
