"""Second-round tournament using first-round survivor identities."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .tournament_lab import run_adversarial_tournament


@dataclass(frozen=True, slots=True)
class RoundTwoResult:
    worlds: int
    selected: int
    unresolved: int
    failed: int
    winners: tuple[tuple[str, int], ...]


def run_round_two() -> RoundTwoResult:
    report = run_adversarial_tournament()
    counts = Counter(
        audit.result.decision.selected_model_id
        for audit in report.audits
        if audit.result.decision.selected_model_id is not None
    )
    return RoundTwoResult(
        worlds=len(report.audits),
        selected=len(report.selected),
        unresolved=len(report.unresolved),
        failed=len(report.failures),
        winners=tuple(sorted(counts.items(), key=lambda x: (-x[1], x[0] or ""))),
    )


def render(result: RoundTwoResult | None = None) -> str:
    result = result or run_round_two()
    lines = [
        "TIAMAT TOURNAMENT ROUND 2",
        f"worlds={result.worlds}",
        f"selected={result.selected}",
        f"unresolved={result.unresolved}",
        f"failures={result.failed}",
        "winners:",
    ]
    lines.extend(f"  {name}: {count}" for name, count in result.winners)
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
