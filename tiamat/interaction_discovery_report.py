"""Small executable report for blind interaction discovery."""
from __future__ import annotations

import numpy as np

from tiamat.interaction_discovery import discover_interactions, format_report


def synthetic_raw_panel(n: int = 400, seed: int = 20260811):
    rng = np.random.default_rng(seed)
    a = rng.random(n)
    b = rng.random(n)
    c = rng.random(n)
    d = rng.normal(size=n)
    # Hidden relationship: XOR of thresholded A/B. Names are deliberately opaque.
    y = ((a > 0.5) ^ (b > 0.5)).astype(int)
    return {
        "probe_01": a,
        "probe_02": b,
        "probe_03": c,
        "probe_04": d,
    }, y


def main() -> None:
    signals, labels = synthetic_raw_panel()
    results = discover_interactions(signals, labels, shuffle_trials=20)
    print(format_report(results))
    promoted = [r for r in results if r.promoted]
    print(f"promoted_pairs={len(promoted)}")
    for result in promoted:
        print(f"DISCOVERED {result.left}+{result.right} relation={result.relation}")


if __name__ == "__main__":
    main()
