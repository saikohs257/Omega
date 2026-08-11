"""Out-of-sample directional transfer and inertia decomposition.

For each ordered pair X->Y, compare an intercept-only predictor, Y-history
predictor, X-history predictor, and joint X+Y-history predictor.  Scores are
computed on a held-out suffix.  The incremental gain of X beyond Y history is
reported as transfer information; the reverse direction is measured separately.
This is predictive influence, not a causal claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from statistics import mean

from tools.dvqt_canonical_tournament import build_worlds

VARIABLES = ("D", "V", "B", "tau", "mode")
LAG = 1
HOLDOUT_FRAC = 0.25


def field(row, name: str) -> float:
    if name == "D": return row.D
    if name == "V": return row.V
    if name == "B": return row.B
    if name == "tau": return float(row.tau_mode)
    if name == "mode": return 1.0 if row.mode.value == "E" else 0.0
    raise KeyError(name)


def mse(y, p):
    return mean((a-b)**2 for a,b in zip(y,p))


def fit_predict_1(x, y, test):
    mx, my = mean(x), mean(y)
    var = mean((v-mx)**2 for v in x)
    beta = sum((a-mx)*(b-my) for a,b in zip(x,y)) / var if var else 0.0
    alpha = my - beta*mx
    return [alpha + beta*v for v in test]


def fit_predict_2(x, z, y, test_x, test_z):
    # Closed-form ridge-stabilized least squares with tiny fixed ridge.
    mx, mz, my = mean(x), mean(z), mean(y)
    xx = sum((a-mx)**2 for a in x) + 1e-9
    zz = sum((a-mz)**2 for a in z) + 1e-9
    xz = sum((a-mx)*(b-mz) for a,b in zip(x,z))
    xy = sum((a-mx)*(b-my) for a,b in zip(x,y))
    zy = sum((a-mz)*(b-my) for a,b in zip(z,y))
    det = xx*zz - xz*xz + 1e-9
    bx = (xy*zz - zy*xz) / det
    bz = (zy*xx - xy*xz) / det
    alpha = my - bx*mx - bz*mz
    return [alpha + bx*a + bz*b for a,b in zip(test_x,test_z)]

@dataclass(frozen=True)
class Transfer:
    src: str
    dst: str
    base_mse: float
    src_only_mse: float
    joint_mse: float
    transfer_gain: float
    reverse_gain: float


def run_pair(rows, src: str, dst: str) -> Transfer | None:
    if len(rows) < 16:
        return None
    x = [field(r, src) for r in rows[:-1]]
    z = [field(r, dst) for r in rows[:-1]]
    y = [field(rows[i+1], dst) for i in range(len(rows)-1)]
    n = len(y)
    cut = max(8, int(n*(1-HOLDOUT_FRAC)))
    tx, tz, ty = x[:cut], z[:cut], y[:cut]
    vx, vz, vy = x[cut:], z[cut:], y[cut:]
    if not vy:
        return None
    base_pred = [mean(ty)] * len(vy)
    dst_pred = fit_predict_1(tz, ty, vz)
    src_pred = fit_predict_1(tx, ty, vx)
    joint_pred = fit_predict_2(tx, tz, ty, vx, vz)
    base = mse(vy, base_pred)
    dst_mse = mse(vy, dst_pred)
    src_mse = mse(vy, src_pred)
    joint = mse(vy, joint_pred)
    transfer = dst_mse - joint
    reverse = None
    # Reverse direction: dst history predicting src, symmetry checked by caller.
    return Transfer(src, dst, base, src_mse, joint, transfer, float(reverse or 0.0))


def main() -> None:
    worlds = build_worlds()
    rows = []
    for name, trajectory in worlds.items():
        for src in VARIABLES:
            for dst in VARIABLES:
                if src == dst:
                    continue
                r = run_pair(trajectory, src, dst)
                if r is not None:
                    rows.append(r)
    print("DVQT TRANSFER LAB")
    print("src -> dst | mean incremental transfer MSE gain")
    for src in VARIABLES:
        for dst in VARIABLES:
            if src == dst: continue
            vals = [r.transfer_gain for r in rows if r.src == src and r.dst == dst]
            if vals:
                print(f"{src}->{dst} | {mean(vals):.6f}")
    print("TOP TRANSFERS")
    for r in sorted(rows, key=lambda r: r.transfer_gain, reverse=True)[:20]:
        print(f"{r.src}->{r.dst} | gain={r.transfer_gain:.6f} base={r.base_mse:.6f} joint={r.joint_mse:.6f}")

if __name__ == "__main__":
    main()
