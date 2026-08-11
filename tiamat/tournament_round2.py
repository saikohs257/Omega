"""Progressive second round: stress first-round winners with semantic attacks."""
from __future__ import annotations

from dataclasses import dataclass

from .adversarial_elimination import eliminate_winner
from .model_selection import ModelMetrics
from .tournament_lab import run_adversarial_tournament
from .world_lab import build_world_lab


@dataclass(frozen=True, slots=True)
class RoundTwoAudit:
    world: str
    candidate: str
    survived: tuple[str, ...]
    failed: tuple[str, ...]
    expected_kills: tuple[str, ...]
    delayed_status: str
    variant_metrics: tuple[tuple[str, tuple[ModelMetrics, ...]], ...]

    @property
    def passed(self) -> bool:
        # Inversion is a deliberate kill test. Attenuation is the robustness
        # gate. Delay is diagnostic and can never eliminate a candidate.
        return "attenuated" in self.survived and "inverse" in self.failed


@dataclass(frozen=True, slots=True)
class RoundTwoResult:
    worlds: int
    first_round_selected: int
    stressed: int
    survivors: tuple[str, ...]
    audits: tuple[RoundTwoAudit, ...]

    @property
    def failed(self) -> int:
        return sum(1 for audit in self.audits if not audit.passed)


def run_round_two() -> RoundTwoResult:
    """Run Round 1, then stress only its selected winners."""
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
            expected_kills=("inverse",),
            delayed_status=result.delayed_status,
            variant_metrics=tuple((a.variant, a.metrics) for a in result.audits),
        )
        audits.append(item)
        if item.passed:
            survivors.append(winner)

    return RoundTwoResult(
        worlds=len(report.audits),
        first_round_selected=len(report.selected),
        stressed=len(audits),
        survivors=tuple(sorted(set(survivors))),
        audits=tuple(audits),
    )


def _metric_line(metric: ModelMetrics) -> str:
    return (
        f"    {metric.model_id}: auc={metric.auc:.6f} brier={metric.brier:.6f} "
        f"log_loss={metric.log_loss:.6f} stability={metric.stability:.6f} "
        f"calibration_error={metric.calibration_error:.6f} "
        f"brier_skill={metric.brier_skill:.6f} complexity={metric.complexity} "
        f"score={metric.score:.6f} n={metric.evaluated_n}"
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
            f"WORLD {audit.world} | candidate={audit.candidate} | "
            f"passed={audit.passed} | delayed={audit.delayed_status}"
        )
        for variant, metrics in audit.variant_metrics:
            lines.append(f"  VARIANT {variant}")
            for metric in metrics:
                lines.append(_metric_line(metric))
    lines.append("SURVIVORS=" + ",".join(result.survivors))
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
