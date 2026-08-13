"""Head-local mechanism ablation court.

Research-only. This deliberately does not grant runtime authority. It loads
historical head-local evidence and records leave-one-variable-out / pairwise
mechanism comparisons where the corresponding evidence is available.

The court keeps historical head-local targets separate from the common
15-hour structural target; those targets must never be merged into one score.
"""
from __future__ import annotations

from dataclasses import dataclass

HEADS = ("H0", "H2", "H3", "H4", "ExitBridge", "PriorCarry")

@dataclass(frozen=True)
class AblationSpec:
    head: str
    target: str
    required: tuple[str, ...]

SPECS = (
    AblationSpec("H0", "historical_0_to_4_target", ("LiveDeficit", "hazard_raw", "SimpleShock")),
    AblationSpec("H2", "historical_2_to_4_target", ("LiveDeficit", "hazard_raw", "SimpleShock")),
    AblationSpec("H3", "historical_3_to_4_target", ("LiveDeficit", "hazard_raw", "SimpleShock")),
    AblationSpec("H4", "historical_4_to_4_target", ("LiveDeficit", "hazard_raw", "SimpleShock")),
    AblationSpec("ExitBridge", "future_reentry_timing", ("exit_state", "timers")),
    AblationSpec("PriorCarry", "future_reentry_timing", ("previous_state",)),
)

def main() -> None:
    print("TIAMAT HEAD LOCAL ABLATION COURT")
    print("status=research-only; authority=none")
    for spec in SPECS:
        print(f"HEAD={spec.head} TARGET={spec.target} REQUIRED={','.join(spec.required)}")
    print("NEXT_EVIDENCE_GATE=run historical leave-one-variable-out and contamination tests")
    print("IMPORTANT=do not substitute the common 15h structural target for historical head-local targets")

if __name__ == "__main__":
    main()
