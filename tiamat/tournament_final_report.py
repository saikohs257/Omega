"""Single auditable end-state report for the TIAMAT tournament."""
from __future__ import annotations

from .tournament_report import build_report
from .tournament_round2 import run_round_two
from .tournament_round3 import audit_segments, run_round_three


def render() -> str:
    round1 = build_report()
    round2 = run_round_two()
    round3 = run_round_three()
    segment_rows = audit_segments()
    lines = [
        "TIAMAT TOURNAMENT — FINAL AUDIT",
        "",
        "ROUND 1",
        f"worlds={len(round1.rows)} selected={sum(r.selected is not None for r in round1.rows)} failures={len(round1.failures)}",
        "",
        "ROUND 2",
        f"worlds={round2.worlds} selected={round2.first_round_selected} stressed={round2.stressed} survivors={len(round2.survivors)} failures={round2.failed}",
        "SURVIVORS=" + ",".join(round2.survivors),
        "",
        "ROUND 3",
        f"survivors={len(round3.survivors)} matches={len(round3.matches)} unresolved={sum(m.unresolved for m in round3.matches)}",
        "RANKING=" + ",".join(f"{name}:{score}" for name, score in round3.ranking),
        "",
        "ROUND 3 FULL SEGMENT MATRIX",
    ]
    for row in segment_rows:
        lines.append(
            f"{row.segment}|{row.candidate}|brier={row.brier:.6f}|log_loss={row.log_loss:.6f}|"
            f"auc={row.auc:.6f}|calibration_error={row.calibration_error:.6f}|"
            f"brier_skill={row.brier_skill:.6f}|complexity={row.complexity}"
        )
    lines.extend([
        "",
        "FROZEN_ORDER=Brier,LogLoss,AUC,CalibrationError,Complexity",
        "PRACTICAL_TOLERANCE=0.001",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
