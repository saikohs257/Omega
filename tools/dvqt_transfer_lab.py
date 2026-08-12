"""Out-of-sample directional transfer with temporal surrogate controls.

The first transfer implementation was scale-normalized but still too permissive:
DVQT trajectories share a deterministic latent clock, so nearly every source
could appear to explain nearly all of a destination. This version keeps the
chronological held-out test but adds a phase-preserving circular-shift null for
the source. The interpretable quantity is therefore observed incremental gain
above the source's own temporal-alignment null. Directionality is the paired
forward-minus-reverse null-adjusted gain. This is predictive influence, not
causal proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median, pstdev

from tools.dvqt_canonical_tournament import build_worlds

VARIABLES = ("D", "V", "B", "tau", "mode")
HOLDOUT_FRAC = 0.25
MIN_TRAIN = 8
MIN_LEN = 16
MIN_SHIFT = 3
_EPS = 1e-12


def field(row, name: str) -> float:
    if name == "D": return float(row.D)
    if name == "V": return float(row.V)
    if name == "B": return float(row.B)
    if name == "tau": return float(row.tau_mode)
    if name == "mode": return 1.0 if row.mode.value == "E" else 0.0
    raise KeyError(name)


def mse(y, p) -> float:
    return mean((a - b) ** 2 for a, b in zip(y, p))


def fit_predict_1(x, y, test):
    mx, my = mean(x), mean(y)
    var = mean((v - mx) ** 2 for v in x)
    beta = sum((a - mx) * (b - my) for a, b in zip(x, y)) / var if var > _EPS else 0.0
    alpha = my - beta * mx
    return [alpha + beta * v for v in test]


def fit_predict_2(x, z, y, test_x, test_z):
    """Centered two-variable least squares with a numerical ridge."""
    mx, mz, my = mean(x), mean(z), mean(y)
    xx = sum((a - mx) ** 2 for a in x) + _EPS
    zz = sum((a - mz) ** 2 for a in z) + _EPS
    xz = sum((a - mx) * (b - mz) for a, b in zip(x, z))
    xy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    zy = sum((a - mz) * (b - my) for a, b in zip(z, y))
    det = xx * zz - xz * xz
    if abs(det) <= _EPS:
        return fit_predict_1(z, y, test_z)
    bx = (xy * zz - zy * xz) / det
    bz = (zy * xx - xy * xz) / det
    alpha = my - bx * mx - bz * mz
    return [alpha + bx * a + bz * b for a, b in zip(test_x, test_z)]


def _split(xs, zs, ys):
    n = len(ys)
    cut = max(MIN_TRAIN, int(n * (1 - HOLDOUT_FRAC)))
    if cut >= n:
        return None
    return xs[:cut], zs[:cut], ys[:cut], xs[cut:], zs[cut:], ys[cut:]


def normalized_gain(x, z, y) -> float:
    parts = _split(x, z, y)
    if parts is None:
        return 0.0
    tx, tz, ty, vx, vz, vy = parts
    base = mse(vy, fit_predict_1(tz, ty, vz))
    joint = mse(vy, fit_predict_2(tx, tz, ty, vx, vz))
    return (base - joint) / max(base, _EPS)


def circular_null_gains(x, z, y) -> list[float]:
    """Destroy source/destination phase alignment while preserving source order."""
    n = len(x)
    max_shift = n - MIN_SHIFT
    if max_shift <= MIN_SHIFT:
        return []
    vals = []
    for shift in range(MIN_SHIFT, max_shift + 1):
        shifted = x[shift:] + x[:shift]
        vals.append(normalized_gain(shifted, z, y))
    return vals


@dataclass(frozen=True)
class Transfer:
    world: str
    src: str
    dst: str
    observed_gain: float
    null_median: float
    null_mean: float
    excess_gain: float
    null_sd: float
    null_n: int


def run_pair(world: str, rows, src: str, dst: str) -> Transfer | None:
    if len(rows) < MIN_LEN:
        return None

    x = [field(r, src) for r in rows[:-1]]
    z = [field(r, dst) for r in rows[:-1]]
    y = [field(rows[i + 1], dst) for i in range(len(rows) - 1)]

    observed = normalized_gain(x, z, y)
    nulls = circular_null_gains(x, z, y)
    if not nulls:
        return None
    nm = median(nulls)
    return Transfer(
        world,
        src,
        dst,
        observed,
        nm,
        mean(nulls),
        observed - nm,
        pstdev(nulls) if len(nulls) > 1 else 0.0,
        len(nulls),
    )


def summarize(values) -> tuple[float, float, float, int]:
    vals = list(values)
    if not vals:
        return 0.0, 0.0, 0.0, 0
    return mean(vals), median(vals), pstdev(vals) if len(vals) > 1 else 0.0, len(vals)


def main() -> None:
    worlds = build_worlds()
    rows = []
    for name, trajectory in worlds.items():
        for src in VARIABLES:
            for dst in VARIABLES:
                if src == dst:
                    continue
                result = run_pair(name, trajectory, src, dst)
                if result is not None:
                    rows.append(result)

    print("DVQT TRANSFER LAB")
    print("observed = normalized conditional gain on chronological 75/25 holdout")
    print("null = median gain under circular source shifts; preserves source autocorrelation")
    print("excess = observed - null; directionality = paired excess-gap")
    print("\nORDERED TRANSFERS")
    for src in VARIABLES:
        for dst in VARIABLES:
            if src == dst:
                continue
            vals = [r.excess_gain for r in rows if r.src == src and r.dst == dst]
            if vals:
                m, med, sd, n = summarize(vals)
                obs = mean(r.observed_gain for r in rows if r.src == src and r.dst == dst)
                nul = mean(r.null_median for r in rows if r.src == src and r.dst == dst)
                print(f"{src}->{dst} | observed={obs:.6f} null={nul:.6f} excess={m:.6f} median_excess={med:.6f} sd={sd:.6f} n={n}")

    print("\nDIRECTIONAL ASYMMETRY (excess forward - excess reverse)")
    for i, src in enumerate(VARIABLES):
        for dst in VARIABLES[i + 1:]:
            fwd = {r.world: r.excess_gain for r in rows if r.src == src and r.dst == dst}
            rev = {r.world: r.excess_gain for r in rows if r.src == dst and r.dst == src}
            gaps = [fwd[w] - rev[w] for w in fwd.keys() & rev.keys()]
            if gaps:
                m, med, sd, n = summarize(gaps)
                print(f"{src}->{dst} vs {dst}->{src} | mean_gap={m:.6f} median_gap={med:.6f} sd={sd:.6f} n={n}")

    print("\nTOP DIRECTIONAL EDGES")
    edges = []
    for i, src in enumerate(VARIABLES):
        for dst in VARIABLES[i + 1:]:
            fwd = {r.world: r.excess_gain for r in rows if r.src == src and r.dst == dst}
            rev = {r.world: r.excess_gain for r in rows if r.src == dst and r.dst == src}
            for world in fwd.keys() & rev.keys():
                gap = fwd[world] - rev[world]
                edges.append((abs(gap), gap, world, src, dst, fwd[world], rev[world]))
    for _, gap, world, src, dst, forward, reverse in sorted(edges, reverse=True)[:20]:
        print(f"{world}: {src}->{dst} gap={gap:.6f} forward={forward:.6f} reverse={reverse:.6f}")


if __name__ == "__main__":
    main()
