"""Complete evidence ledger for every TIAMAT tournament round.

This is an observation/reporting layer only. It never changes selection rules.
It records every AUC, Brier, log loss, calibration error, Brier skill,
stability, complexity, and composite score for every candidate actually tested
in every world/variant/pairwise matchup.
"""
from __future__ import annotations

from .adversarial_worlds import build_adversarial_worlds
from .model_selection import CandidateSpec, ModelMetrics, evaluate_candidate
from .tournament_lab import run_adversarial_tournament
from .tournament_round2 import run_round_two
from .tournament_round3 import audit_segments, run_round_three


def _metric_line(metric: ModelMetrics) -> str:
    return (
        f"{metric.model_id}: auc={metric.auc:.6f} brier={metric.brier:.6f} "
        f"log_loss={metric.log_loss:.6f} stability={metric.stability:.6f} "
        f"calibration_error={metric.calibration_error:.6f} "
        f"brier_skill={metric.brier_skill:.6f} complexity={metric.complexity} "
        f"score={metric.score:.6f} n={metric.evaluated_n}"
    )


def render_full_audit() -> str:
    worlds = build_adversarial_worlds()
    lab = run_adversarial_tournament()
    round2 = run_round_two()
    round3 = run_round_three()
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
            f"delay={audit.delayed_status} failed={','.join(audit.failed) or '-'}"
        )
        for variant, metrics in audit.variant_metrics:
            lines.append(f"  VARIANT {variant}")
            for metric in metrics:
                lines.append("    " + _metric_line(metric))

    lines.append("")
    lines.append("=== ROUND 3: COMMON HELD-OUT PANEL / EVERY SURVIVOR ===")
    lines.append(
        "comparison_order=Brier,LogLoss,AUC,CalibrationError,Complexity "
        f"survivors={len(round3.survivors)}"
    )
    lines.append("survivors=" + ",".join(round3.survivors))
    for candidate in round3.survivors:
        # Use the exact common-panel evaluator that determines the tournament.
        from .tournament_round3 import _common_panel, _metrics
        labels, panel, _ = _common_panel()
        metric = _metrics(candidate, panel[candidate], labels)
        lines.append("  " + _metric_line(metric))

    lines.append("ROUND 3 SEGMENTS")
    for row in audit_segments():
        lines.append(
            f"  SEGMENT {row.segment} CANDIDATE {row.candidate}: "
            f"auc={row.auc:.6f} brier={row.brier:.6f} log_loss={row.log_loss:.6f} "
            f"calibration_error={row.calibration_error:.6f} brier_skill={row.brier_skill:.6f} "
            f"complexity={row.complexity}"
        )

    lines.append("ROUND 3 HEAD-TO-HEAD")
    for match in round3.matches:
        lines.append(
            f"MATCH {match.a} vs {match.b}: {match.a_wins}-{match.b_wins}, "
            f"ties={match.ties}, unresolved={match.unresolved}"
        )

    lines.append("RANKING")
    lines.extend(f"{name}: {score}" for name, score in round3.ranking)

    lines.append("")
    lines.append("=== ROUND 2 SUMMARY ===")
    lines.append(f"selected={round2.first_round_selected} stressed={round2.stressed} survivors={len(round2.survivors)}")
    lines.append("survivors=" + ",".join(round2.survivors))
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_full_audit())
