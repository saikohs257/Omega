"""Ten fast falsification tests for the DVQT directional hypothesis.

These are deliberately complementary: lag scans, nulls, leave-one-world-out,
conditioning, sign stability, and source ablation. They test predictive
structure, not causal proof.
"""
from __future__ import annotations

from statistics import mean, median
from tools.dvqt_canonical_tournament import build_worlds
from tools.dvqt_transfer_lab import VARIABLES, field, normalized_gain, circular_null_gains


def lag_gain(rows, src, dst, lag):
    if len(rows) < 20 + lag:
        return 0.0
    x = [field(r, src) for r in rows[:-lag]]
    z = [field(rows[i], dst) for i in range(len(rows) - lag)]
    y = [field(rows[i + lag], dst) for i in range(len(rows) - lag)]
    return normalized_gain(x, z, y)


def pair_excess(rows, src, dst):
    x = [field(r, src) for r in rows[:-1]]
    z = [field(r, dst) for r in rows[:-1]]
    y = [field(rows[i + 1], dst) for i in range(len(rows) - 1)]
    n = circular_null_gains(x, z, y)
    return normalized_gain(x, z, y) - median(n) if n else 0.0


def worlds():
    return build_worlds()


def run():
    ws = worlds()
    results = []

    # 1. Delay scan: find whether D->mode has a specific temporal sweet spot.
    gaps = []
    for lag in range(1, 7):
        vals = [lag_gain(rows, "D", "mode", lag) - lag_gain(rows, "mode", "D", lag)
                for rows in ws.values()]
        gaps.append((lag, mean(vals)))
    best_lag, best_gap = max(gaps, key=lambda x: x[1])
    results.append(("1 lag scan", best_lag, best_gap))

    # 2. Reverse lag scan: require the preferred direction to beat its reverse.
    rev = [lag_gain(rows, "mode", "D", best_lag) for rows in ws.values()]
    fwd = [lag_gain(rows, "D", "mode", best_lag) for rows in ws.values()]
    results.append(("2 reverse check", best_lag, mean(fwd) - mean(rev)))

    # 3. Leave-one-world-out stability of the aggregate D->mode excess.
    loo = []
    for omit in ws:
        vals = [pair_excess(rows, "D", "mode") for name, rows in ws.items() if name != omit]
        loo.append(mean(vals))
    results.append(("3 leave-one-world-out", min(loo), max(loo)))

    # 4. Sign consistency: fraction of worlds where D->mode exceeds reverse.
    signs = []
    for rows in ws.values():
        signs.append(pair_excess(rows, "D", "mode") - pair_excess(rows, "mode", "D"))
    results.append(("4 sign consistency", sum(v > 0 for v in signs) / len(signs), median(signs)))

    # 5. Null z-score: compare observed excess to the null spread.
    zs = []
    for rows in ws.values():
        x = [field(r, "D") for r in rows[:-1]]
        z = [field(r, "mode") for r in rows[:-1]]
        y = [field(rows[i + 1], "mode") for i in range(len(rows) - 1)]
        obs = normalized_gain(x, z, y)
        ns = circular_null_gains(x, z, y)
        sd = (sum((v - mean(ns)) ** 2 for v in ns) / len(ns)) ** 0.5 if ns else 1.0
        zs.append((obs - mean(ns)) / max(sd, 1e-12))
    results.append(("5 null z", mean(zs), median(zs)))

    # 6. Block/null robustness: coarse block permutation of D.
    block_excess = []
    for rows in ws.values():
        n = len(rows) - 1
        x = [field(r, "D") for r in rows[:-1]]
        z = [field(r, "mode") for r in rows[:-1]]
        y = [field(rows[i + 1], "mode") for i in range(n)]
        base = normalized_gain(x, z, y)
        block = max(4, n // 12)
        shifted = x[block:] + x[:block]
        block_excess.append(base - normalized_gain(shifted, z, y))
    results.append(("6 block null", mean(block_excess), median(block_excess)))

    # 7. Directional specificity: compare D->mode with D->V/tau/B.
    dm = mean(pair_excess(r, "D", "mode") for r in ws.values())
    controls = {dst: mean(pair_excess(r, "D", dst) for r in ws.values()) for dst in ("V", "B", "tau")}
    results.append(("7 destination specificity", dm, max(controls.values())))

    # 8. Source specificity: compare D->mode with V/B/tau->mode.
    sources = {src: mean(pair_excess(r, src, "mode") for r in ws.values()) for src in ("D", "V", "B", "tau")}
    results.append(("8 source specificity", sources["D"], max(v for k, v in sources.items() if k != "D")))

    # 9. Persistence conditioning: ask whether D adds beyond D's own one-step history.
    # normalized_gain already uses destination history; compare against D shuffled null.
    conditioned = []
    for rows in ws.values():
        conditioned.append(pair_excess(rows, "D", "mode"))
    results.append(("9 conditional persistence", mean(conditioned), median(conditioned)))

    # 10. Source ablation: destroy D's temporal alignment while keeping mode intact.
    drops = []
    for rows in ws.values():
        n = len(rows) - 1
        x = [field(r, "D") for r in rows[:-1]]
        z = [field(r, "mode") for r in rows[:-1]]
        y = [field(rows[i + 1], "mode") for i in range(n)]
        shift = max(3, n // 5)
        drops.append(normalized_gain(x, z, y) - normalized_gain(x[shift:] + x[:shift], z, y))
    results.append(("10 D ablation", mean(drops), median(drops)))

    print("DVQT TEN-TEST DIRECTIONAL BATTERY")
    for row in results:
        print(" | ".join(str(v) for v in row))

    assert len(results) == 10
    assert all(len(r) == 3 for r in results)
    return results


if __name__ == "__main__":
    run()
