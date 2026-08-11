"""Human-readable tournament scorecard for the TIAMAT synthetic laboratories."""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

from .tournament_lab import run_adversarial_tournament


@dataclass(frozen=True, slots=True)
class TournamentScore:
    worlds: int
    selected: int
    unresolved: int
    failed: int
    winner_counts: tuple[tuple[str, int], ...]


def build_scorecard() -> TournamentScore:
    report = run_adversarial_tournament()
    winners = Counter(
        audit.result.decision.selected_model_id
        for audit in report.audits
        if audit.result.decision.selected_model_id is not None
    )
    return TournamentScore(
        worlds=len(report.audits),
        selected=len(report.selected),
        unresolved=len(report.unresolved),
        failed=len(report.failures),
        winner_counts=tuple(sorted(winners.items(), key=lambda item: (-item[1], item[0] or ""))),
    )


def render_scorecard(score: TournamentScore | None = None) -> str:
    score = score or build_scorecard()
    lines = [
        "TIAMAT TOURNAMENT SCORECARD",
        f"worlds={score.worlds}",
        f"selected={score.selected}",
        f"unresolved={score.unresolved}",
        f"failures={score.failed}",
        "winner_counts:",
    ]
    for model_id, count in score.winner_counts:
        lines.append(f"  {model_id}: {count}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_scorecard())
