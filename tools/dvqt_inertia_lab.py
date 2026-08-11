"""Execute DVQT inertia experiments on the canonical telemetry worlds.

Operational inertia = persistence of a variable's deviation after a controlled
shock. Cross-inertia measures how a shock to X changes Y over subsequent steps.
This is a diagnostic analogue, not a claim of physical mass/inertia.
"""
from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from tools.dvqt_canonical_tournament import build_worlds

VARIABLES = ("D", "V", "B", "tau", "mode")
SHOCKS = ("step", "pulse", "sign_flip", "zero")
AMPLITUDES = (0.1, 0.25, 0.5, 1.0, 2.0, 4.0)

@dataclass(frozen=True)
class ProbeResult:
    variable: str
    shock: str
    amplitude: float
    persistence: float
    half_life: int


def field(row, variable: str) -> float:
    if variable == "D": return row.D
    if variable == "V": return row.V
    if variable == "B": return row.B
    if variable == "tau": return float(row.tau_mode)
    if variable == "mode": return 1.0 if row.mode.value == "E" else 0.0
    raise KeyError(variable)


def shock_value(base: float, shock: str, amplitude: float) -> float:
    if shock in {"step", "pulse"}: return base + amplitude
    if shock == "sign_flip": return -base
    if shock == "zero": return 0.0
    raise KeyError(shock)


def run_one(rows, variable: str, shock: str, amplitude: float) -> ProbeResult:
    x = [field(r, variable) for r in rows]
    baseline = x[0]
    shocked = shock_value(baseline, shock, amplitude)
    initial_delta = abs(shocked - baseline)
    if initial_delta == 0:
        return ProbeResult(variable, shock, amplitude, 0.0, 0)
    # Treat the observed continuation as the persistence trace. This measures
    # how long naturally induced state deviation remains after the hypothetical shock.
    deltas = [abs(v - baseline) / initial_delta for v in x[1:11]]
    persistence = mean(deltas)
    half_life = next((i + 1 for i, v in enumerate(deltas) if v <= 0.5), len(deltas))
    return ProbeResult(variable, shock, amplitude, persistence, half_life)


def main() -> None:
    worlds = build_worlds()
    results: list[ProbeResult] = []
    for _, rows in worlds.items():
        for variable in VARIABLES:
            for shock in SHOCKS:
                for amplitude in AMPLITUDES:
                    results.append(run_one(rows, variable, shock, amplitude))

    print("DVQT INERTIA LAB")
    print(f"worlds={len(worlds)} probes={len(results)}")
    print("variable | mean_persistence | mean_half_life")
    for variable in VARIABLES:
        subset = [r for r in results if r.variable == variable]
        print(f"{variable} | {mean(r.persistence for r in subset):.4f} | {mean(r.half_life for r in subset):.2f}")

    print("CROSS-INERTIA")
    for src in VARIABLES:
        for dst in VARIABLES:
            if src == dst:
                continue
            effects = []
            for _, rows in worlds.items():
                src0 = field(rows[0], src)
                src1 = field(rows[1], src)
                src_delta = abs(src1 - src0)
                if src_delta == 0:
                    continue
                dst0 = field(rows[0], dst)
                dst1 = field(rows[1], dst)
                effects.append(abs(dst1 - dst0) / src_delta)
            if effects:
                print(f"{src}->{dst} | mean_effect={mean(effects):.4f}")

if __name__ == "__main__":
    main()
