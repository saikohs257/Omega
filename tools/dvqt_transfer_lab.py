"""Out-of-sample directional transfer and inertia decomposition.

For each ordered pair X->Y, compare Y-history alone with Y-history+X-history
on a chronological held-out suffix. The primary transfer score is the relative
reduction in destination-history MSE, so variables with larger numeric scale do
not dominate the result. Directionality is the forward normalized gain minus the
reverse normalized gain. This is predictive influence, not causal proof.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, median, pstdev

from tools.dvqt_canonical_tournament import build_worlds

VARIABLES = ("D", "V", "B", "tau", "mode")
HOLDOUT_FRAC = 0.25
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
    """Centered two-variable least squares with a tiny numerical ridge."""
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


@dataclass(frozen=True)
class Transfer:
    world: str
    src: str
    dst: str
    dst_history_mse: float
    joint_mse: float
    raw_gain: float
    normalized_gain: float


def run_pair(world: str, rows, src: str, dst: str) -> Transfer | None:
    if len(rows) < 16:
        return None

    # X_t, Y_t -> predict Y_{t+1}. All splits remain chronological.
    x = [field(r, src) for r in rows[:-1]]
    z = [field(r, dst) for r in rows[:-1]]
    y = [field(rows[i + 1], dst) for i in range(len(rows) - 1)]

    n = len(y)
    cut = max(8, int(n * (1 - HOLDOUT_FRAC)))
    tx, tz, ty = x[:cut], z[:cut], y[:cut]
    vx, vz, vy = x[cut:], z[cut:], y[cut:]
    if not vy:
        return None

    dst_pred = fit_predict_1(tz, ty, vz)
    joint_pred = fit_predict_2(tx, tz, ty, vx, vz)
    dst_mse = mse(vy, dst_pred)
    joint = mse(vy, joint_pred)
    raw = dst_mse - joint
    normalized = raw / max(dst_mse, _EPS)
    return Transfer(world, src, dst, dst_mse, joint, raw, normalized)


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
                if src != dst:
                    r = run_pair(name, trajectory, src, dst)
                    if r is not None:
                        rows.append(r)

    print("DVQT TRANSFER LAB")
    print("metric = normalized conditional transfer gain = (MSE[Y|Yhist] - MSE[Y|Yhist,Xhist]) / MSE[Y|Yhist]")
    print("temporal split = chronological 75/25; no circular lags")
    print("\nORDERED TRANSFERS")
    for src in VARIABLES:
        for dst in VARIABLES:
            if src == dst:
                continue
            vals = [r.normalized_gain for r in rows if r.src == src and r.dst == dst]
            if vals:
                m, med, sd, n = summarize(vals)
                print(f"{src}->{dst} | mean={m:.6f} median={med:.6f} sd={sd:.6f} n={n}")

    print("\nDIRECTIONAL ASYMMETRY (forward - reverse)")
    for i, src in enumerate(VARIABLES):
        for dst in VARIABLES[i + 1:]:
            fwd = {r.world: r.normalized_gain for r in rows if r.src == src and r.dst == dst}
            rev = {r.world: r.normalized_gain for r in rows if r.src == dst and r.dst == src}
            gaps = [fwd[w] - rev[w] for w in fwd.keys() & rev.keys()]
            if gaps:
                m, med, sd, n = summarize(gaps)
                print(f"{src}->{dst} vs {dst}->{src} | mean_gap={m:.6f} median_gap={med:.6f} sd={sd:.6f} n={n}")

    print("\nTOP DIRECTIONAL EDGES")
    edges = []
    for i, src in enumerate(VARIABLES):
        for dst in VARIABLES[i + 1:]:
            fwd = {r.world: r.normalized_gain for r in rows if r.src == src and r.dst == dst}
            rev = {r.world: r.normalized_gain for r in rows if r.src == dst and r.dst == src}
            for w in fwd.keys() & rev.keys():
                edges.append((abs(fwd[w] - rev[w]), fwd[w] - rev[w], w, src, dst, fwd[w], rev[w]))
    for _, gap, world, src, dst, fwd, rev in sorted(edges, reverse=True)[:20]:
        print(f"{world}: {src}->{dst} gap={gap:.6f} forward={fwd:.6f} reverse={rev:.6f}")


if __name__ == "__main__":
    main()
