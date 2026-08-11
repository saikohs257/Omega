"""B intervention audit for the canonical DVQT generator.

This is intentionally a falsification audit. The canonical target is currently
constructed as score = .45 D + .35 V + .20 B. We expose that dependency and
compare counterfactual target equations so a perfect B-containing score cannot
be mistaken for evidence of a hidden discovered state.
"""
from __future__ import annotations

from tools.dvqt_canonical_tournament import _features

N = 96
SEEDS = range(1, 21)


def score(d, v, b):
    return 0.45*d + 0.35*v + 0.20*b


def label(d, v, b):
    return int(score(d, v, b) >= 0.50)


def main():
    rows = []
    for seed in SEEDS:
        for i in range(N):
            d, v, b, tau = _features(seed, i)
            rows.append((d, v, b, label(d, v, b)))

    y = [r[3] for r in rows]
    variants = {
        "full": lambda d,v,b: score(d,v,b),
        "B_held_zero": lambda d,v,b: score(d,v,0.0),
        "B_held_half": lambda d,v,b: score(d,v,0.5),
        "B_held_one": lambda d,v,b: score(d,v,1.0),
        "B_only": lambda d,v,b: 0.20*b,
        "DV_only": lambda d,v,b: 0.45*d+0.35*v,
        "D_only": lambda d,v,b: 0.45*d,
        "V_only": lambda d,v,b: 0.35*v,
    }
    print("B INTERVENTION AUDIT")
    print("canonical_target = 0.45*D + 0.35*V + 0.20*B")
    print(f"n={len(rows)} positives={sum(y)} prevalence={sum(y)/len(y):.4f}")
    for name, fn in variants.items():
        pred = [int(fn(d,v,b) >= 0.50) for d,v,b,_ in rows]
        acc = sum(a == b for a,b in zip(pred,y))/len(y)
        print(f"{name:14s} accuracy={acc:.4f} positive_rate={sum(pred)/len(pred):.4f}")

    print("B is therefore not an unidentified latent quantity in this corpus:")
    print("it is an explicit 20% term in the target-generating equation.")


if __name__ == "__main__":
    main()
