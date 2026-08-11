"""Complete evidence ledger for every TIAMAT tournament round.

This is an observation/reporting layer only. It never changes selection rules.
It records every AUC, Brier, log loss, calibration error, Brier skill,
stability, complexity, and composite score for every candidate actually tested
in every world/variant/pairwise matchup.
"""
from __future__ import annotations

from itertools import combinations

from .adversarial_worlds import build_adversarial_worlds
from .model_selection import CandidateSpec, ModelMetrics, evaluate_candidate
from .tournament_lab import run_adversarial_tournament
from .tournament_round2 import run_round_two


def _metric_line(metric: ModelMetrics) -> str:
    return (
        f"{metric.model_id}: auc={metric.auc:.6f} brier={metric.brier:.6f} "
        f"log_loss={metric.log_loss:.6f} stability={metric.stability:.6f} "
        f"calibration_error={metric.calibration_error:.6f} "
        f"brier_skill={metric.brier_skill:.6f} complexity={metric.complexity} "
        f"score={metric.score:.6f} n={metric.evaluated_n}"
    )


def _metrics(labels: tuple[int, ...], predictions: dict[str, tuple[float, ...]]) -> tuple[ModelMetrics, ...]:
    return tuple(
        evaluate_candidate(CandidateSpec(name, (name,)), values, labels)
        for name, values in predictions.items()
    )


def render_full_audit() -> str:
    worlds = build_adversarial_worlds()
    lab = run_adversarial_tournament()
    round2 = run_round_two()
    lines: list[str] = ["TIAMAT COMPLETE TOURNAMENT EVIDENCE AUDIT", ""]

    lines.append("=== ROUND 1: EVERY WORLD / EVERY CANDIDATE ===")
    for world in worlds:
        audit = next(a for a in lab.audits if a.expectation.world_name == world.name)
        lines.append(
            f"WORLD {world.name} | selected={audit.result.decision.selected_model_id or '-'} "
            f"status={audit.result.decision.status} expected={world.truth_mechanism} pass={audit.expectation_met}"
        )
        for metric in audit.result.report.evaluated:
            lines.append("  " + _metric_line(metric.metrics))

    lines.append("")
    lines.append("=== ROUND 2: EVERY SELECTED WORLD / EVERY VARIANT / EVERY CANDIDATE ===")
    for audit in round2.audits:
        lines.append(
            f"WORLD {audit.world} | target={audit.candidate} | passed={audit.passed} "
            f"delay={audit.delayed_status}"
        )
        for variant, metrics in audit.variant_metrics:
            lines.append(f"  VARIANT {variant}")
            for metric in metrics:
                lines.append("    " + _metric_line(metric))

    lines.append("")
    lines.append("=== ROUND 3: EVERY SURVIVOR PAIR / EVERY WORLD ===")
    survivors = tuple(sorted(set(round2.survivors)))
    for a, b in combinations(survivors, 2):
        lines.append(f"MATCH {a} vs {b}")
        for world in worlds:
            if a not in world.predictions or b not in world.predictions:
                lines.append(f"  WORLD {world.name} | unresolved=missing_candidate")
                continue
            ma = evaluate_candidate(CandidateSpec(a, (a,)), world.predictions[a], world.labels)
            mb = evaluate_candidate(CandidateSpec(b, (b,)), world.predictions[b], world.labels)
            key_a = (ma.score, ma.auc, ma.brier_skill, -ma.brier, -ma.log_loss, -ma.complexity)
            key_b = (mb.score, mb.auc, mb.brier_skill, -mb.brier, -mb.log_loss, -mb.complexity)
            winner = a if key_a > key_b else b if key_b > key_a else "TIE"
            lines.append(f"  WORLD {world.name} | winner={winner}")
            lines.append("    " + _metric_line(ma))
            lines.append("    " + _metric_line(mb))

    lines.append("")
    lines.append("=== ROUND 2 SUMMARY ===")
    lines.append(f"selected={round2.first_round_selected} stressed={round2.stressed} survivors={len(round2.survivors)}")
    lines.append("survivors=" + ",".join(round2.survivors))
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_full_audit())
