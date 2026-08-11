"""Auditable tournament report and survivor extraction for TIAMAT labs."""
from __future__ import annotations

from dataclasses import dataclass

from .tournament_lab import run_adversarial_tournament


@dataclass(frozen=True, slots=True)
class TournamentRow:
    world: str
    status: str
    selected: str | None
    expected: str
    expectation_met: bool


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
    return TournamentReport(
        rows=tuple(
            TournamentRow(
                world=a.expectation.world_name,
                status=a.result.decision.status,
                selected=a.result.decision.selected_model_id,
                expected=a.expectation.truth_mechanism,
                expectation_met=a.expectation_met,
            )
            for a in lab.audits
        )
    )


def render_report(report: TournamentReport | None = None) -> str:
    report = report or build_report()
    lines = ["TIAMAT TOURNAMENT REPORT", "world | status | selected | expected | pass"]
    lines.extend(
        f"{row.world} | {row.status} | {row.selected or '-'} | {row.expected} | {row.expectation_met}"
        for row in report.rows
    )
    lines.append("survivors=" + ",".join(report.survivors))
    lines.append("failures=" + str(len(report.failures)))
    return "\n".join(lines)
