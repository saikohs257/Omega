"""Auditable tournament report with complete per-world evidence metrics."""
from __future__ import annotations

from dataclasses import dataclass

from .model_selection import ModelMetrics
from .tournament_lab import run_adversarial_tournament


@dataclass(frozen=True, slots=True)
class MetricRow:
    world: str
    candidate: str
    metrics: ModelMetrics


@dataclass(frozen=True, slots=True)
class TournamentRow:
    world: str
    status: str
    selected: str | None
    expected: str
    expectation_met: bool
    metrics: tuple[MetricRow, ...]


@dataclass(frozen=True, slots=True)
class TournamentReport:
    rows: tuple[TournamentRow, ...]

    @property
    def survivors(self) -> tuple[str, ...]:
        counts: dict[str, int] = {}
        for row in self.rows:
            if row.selected is not None and row.expectation_met:
                counts[row.selected] = counts.get(row.selected, 0) + 1
        return tuple(sorted(counts, key=lambda model: (-counts[model], model)))

    @property
    def failures(self) -> tuple[TournamentRow, ...]:
        return tuple(row for row in self.rows if not row.expectation_met)


def build_report() -> TournamentReport:
    lab = run_adversarial_tournament()
    rows: list[TournamentRow] = []
    for audit in lab.audits:
        metric_rows = tuple(
            MetricRow(audit.expectation.world_name, result.spec.model_id, result.metrics)
            for result in audit.result.report.evaluated
        )
        rows.append(
            TournamentRow(
                world=audit.expectation.world_name,
                status=audit.result.decision.status,
                selected=audit.result.decision.selected_model_id,
                expected=audit.expectation.truth_mechanism,
                expectation_met=audit.expectation_met,
                metrics=metric_rows,
            )
        )
    return TournamentReport(tuple(rows))


def _metric_line(metric: ModelMetrics) -> str:
    return (
        f"  {metric.model_id}: auc={metric.auc:.6f} brier={metric.brier:.6f} "
        f"log_loss={metric.log_loss:.6f} stability={metric.stability:.6f} "
        f"calibration_error={metric.calibration_error:.6f} "
        f"brier_skill={metric.brier_skill:.6f} complexity={metric.complexity} "
        f"score={metric.score:.6f} n={metric.evaluated_n}"
    )


def render_report(report: TournamentReport | None = None) -> str:
    report = report or build_report()
    lines = ["TIAMAT TOURNAMENT REPORT — FULL EVIDENCE", ""]
    for row in report.rows:
        lines.append(
            f"WORLD {row.world} | status={row.status} | selected={row.selected or '-'} "
            f"| expected={row.expected} | pass={row.expectation_met}"
        )
        for metric in row.metrics:
            lines.append(_metric_line(metric.metrics))
    lines.append("")
    lines.append("SURVIVORS=" + ",".join(report.survivors))
    lines.append("FAILURES=" + str(len(report.failures)))
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_report())
