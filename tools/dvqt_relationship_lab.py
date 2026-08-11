from __future__ import annotations

from tools.dvqt_canonical_tournament import build_worlds
from tools.relationship_map import format_report, map_relationships


def target_labels(rows):
    return [1 if rows[i + 1].mode.value == "E" else 0 for i in range(len(rows) - 1)]


def signals(rows):
    current = rows[:-1]
    return {
        "D": [r.D for r in current],
        "V": [r.V for r in current],
        "B": [r.B for r in current],
        "tau": [r.tau_mode for r in current],
        "mode": [1.0 if r.mode.value == "E" else 0.0 for r in current],
    }


def main() -> None:
    worlds = build_worlds()
    all_results = []
    for name, rows in worlds.items():
        results = map_relationships(signals(rows), target_labels(rows), phase=[r.tau_mode for r in rows[:-1]])
        promoted = [r for r in results if r.interaction_gain >= 0.10]
        print(f"WORLD {name} pairs={len(results)} promoted={len(promoted)}")
        print(format_report(results))
        all_results.extend(results)

    if all_results:
        all_results.sort(key=lambda r: (-r.interaction_gain, -abs(r.reverse_gap), -abs(r.lag_gain)))
        print("TOP RELATIONSHIPS ACROSS WORLDS")
        print(format_report(all_results[:20]))


if __name__ == "__main__":
    main()
