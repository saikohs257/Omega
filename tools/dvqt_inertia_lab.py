"""DVQT inertia lab.

Inertia is measured from observed trajectories, not by pretending a shock
changed future rows.  We report persistence/autocorrelation decay and
cross-lag response.  This is a diagnostic analogue, not physical inertia.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from math import sqrt

from tools.dvqt_canonical_tournament import build_worlds

VARIABLES = ("D", "V", "B", "tau", "mode")
MAX_LAG = 10

@dataclass(frozen=True)
class InertiaSummary:
    variable: str
    persistence: float
    half_life: int


def field(row, variable: str) -> float:
    if variable == "D": return row.D
    if variable == "V": return row.V
    if variable == "B": return row.B
    if variable == "tau": return float(row.tau_mode)
    if variable == "mode": return 1.0 if row.mode.value == "E" else 0.0
    raise KeyError(variable)


def corr_at_lag(values: list[float], lag: int) -> float:
    if lag <= 0 or len(values) <= lag + 1:
        return 0.0
    a, b = values[:-lag], values[lag:]
    ma, mb = mean(a), mean(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    den = sqrt(sum(x*x for x in da) * sum(x*x for x in db))
    return (sum(x*y for x, y in zip(da, db)) / den) if den else 0.0


def summarize(rows, variable: str) -> InertiaSummary:
    values = [field(r, variable) for r in rows]
    ac = [max(0.0, corr_at_lag(values, lag)) for lag in range(1, MAX_LAG + 1)]
    persistence = mean(ac)
    half_life = next((lag for lag, value in enumerate(ac, 1) if value <= 0.5), MAX_LAG)
    return InertiaSummary(variable, persistence, half_life)


def cross_lag(rows, src: str, dst: str, lag: int) -> float:
    x = [field(r, src) for r in rows]
    y = [field(r, dst) for r in rows]
    if lag <= 0 or len(x) <= lag + 1:
        return 0.0
    return corr_at_lag(x, lag) if src == dst else _cross_corr(x[:-lag], y[lag:])


def _cross_corr(a: list[float], b: list[float]) -> float:
    ma, mb = mean(a), mean(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    den = sqrt(sum(x*x for x in da) * sum(x*x for x in db))
    return (sum(x*y for x, y in zip(da, db)) / den) if den else 0.0


def main() -> None:
    worlds = build_worlds()
    print("DVQT INERTIA LAB")
    print(f"worlds={len(worlds)}")
    print("variable | mean_positive_autocorrelation | mean_half_life")
    for variable in VARIABLES:
        summaries = [summarize(rows, variable) for rows in worlds.values()]
        print(f"{variable} | {mean(s.persistence for s in summaries):.4f} | {mean(s.half_life for s in summaries):.2f}")

    print("CROSS-LAG RESPONSE (source -> destination, lag 1..10)")
    for src in VARIABLES:
        for dst in VARIABLES:
            if src == dst:
                continue
            vals = [abs(cross_lag(rows, src, dst, lag)) for rows in worlds.values() for lag in range(1, MAX_LAG + 1)]
            if vals:
                print(f"{src}->{dst} | mean_abs_cross_lag={mean(vals):.4f}")

if __name__ == "__main__":
    main()
