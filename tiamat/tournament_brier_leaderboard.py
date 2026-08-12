"""Print the TIAMAT tournament leaderboard using the frozen tournament order.

Primary ordering: Brier (lower is better), then the tournament tie-breakers:
log loss (lower), AUC (higher), calibration error (lower), complexity (lower).
"""
from __future__ import annotations

from .tournament_report import build_report


def main() -> None:
    report = build_report()
    rows = []
    for world in report.rows:
        for metric_row in world.metrics:
            m = metric_row.metrics
            rows.append((m.brier, m.log_loss, -m.auc, m.calibration_error, m.complexity, world.world, m))
    rows.sort(key=lambda x: x[:5])

    print("TIAMAT BRIER LEADERBOARD — TOURNAMENT ORDER")
    print("rank | candidate | world | brier | log_loss | auc | calibration_error | complexity | n")
    for rank, (_, _, _, _, _, world, m) in enumerate(rows, 1):
        print(
            f"{rank:>4} | {m.model_id} | {world} | {m.brier:.6f} | {m.log_loss:.6f} | "
            f"{m.auc:.6f} | {m.calibration_error:.6f} | {m.complexity} | {m.evaluated_n}"
        )


if __name__ == "__main__":
    main()
