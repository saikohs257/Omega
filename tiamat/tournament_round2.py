"""Progressive second round: stress only first-round tournament winners."""
from __future__ import annotations

from dataclasses import dataclass

from .adversarial_elimination import eliminate_winner
from .tournament_lab import run_adversarial_tournament
from .world_lab import build_world_lab


@dataclass(frozen=True, slots=True)
class RoundTwoAudit:
    world: str
    candidate: str
    survived: tuple[str, ...]
    failed: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not self.failed


@dataclass(frozen=True, slots=True)
class RoundTwoResult:
    worlds: int
    first_round_selected: int
    stressed: int
    survivors: tuple[str, ...]
    audits: tuple[RoundTwoAudit, ...]

    @property
    def failed(self) -> int:
        return sum(1 for audit in self.audits if audit.failed)


def run_round_two() -> RoundTwoResult:
    """Run Round 1, then adversarially stress only its selected winners."""
    report = run_adversarial_tournament()
    cases, _ = build_world_lab()
    cases_by_name = {case.name: case for case in cases}
    audits: list[RoundTwoAudit] = []
    survivors: list[str] = []

    for audit in report.selected:
        winner = audit.result.decision.selected_model_id
        if winner is None:
            continue
        case = cases_by_name[audit.expectation.world_name]
        result = eliminate_winner(
            labels=case.labels,
            specs=case.specs,
            predictions=case.heldout_predictions,
            winner=winner,
            max_size=case.max_size,
        )
        item = RoundTwoAudit(
            world=case.name,
            candidate=winner,
            survived=result.survived,
            failed=result.failed,
        )
        audits.append(item)
        if item.passed:
            survivors.append(winner)

    return RoundTwoResult(
        worlds=len(report.audits),
        first_round_selected=len(report.selected),
        stressed=len(audits),
        survivors=tuple(sorted(survivors)),
        audits=tuple(audits),
    )


def render(result: RoundTwoResult | None = None) -> str:
    result = result or run_round_two()
    lines = [
        "TIAMAT TOURNAMENT ROUND 2 — SURVIVOR STRESS",
        f"worlds={result.worlds}",
        f"first_round_selected={result.first_round_selected}",
        f"stressed={result.stressed}",
        f"survivors={len(result.survivors)}",
        f"failed={result.failed}",
    ]
    for audit in result.audits:
        lines.append(
            f"{audit.world}: {audit.candidate} "
            f"survived={','.join(audit.survived) or '-'} "
            f"failed={','.join(audit.failed) or '-'}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
