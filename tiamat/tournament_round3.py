"""Head-to-head tournament for candidates surviving Round 2.

Frozen comparison policy:
1. Brier score (lower is better).
2. Log loss (lower is better).
3. AUC (higher is better).
4. Calibration error (lower is better).
5. Complexity (lower is better).

Differences inside the practical-equivalence tolerances are treated as ties;
we do not manufacture a winner from insignificant decimal differences.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .adversarial_worlds import build_adversarial_worlds
from .model_selection import CandidateSpec, evaluate_candidate
from .tournament_round2 import run_round_two

# Frozen practical-equivalence tolerances. These are intentionally explicit so
# the tournament cannot silently change its decision rule through tuple ordering.
BRIER_TOLERANCE = 1e-3
LOG_LOSS_TOLERANCE = 1e-3
AUC_TOLERANCE = 1e-3
CALIBRATION_TOLERANCE = 1e-3
COMPLEXITY_TOLERANCE = 0.0


@dataclass(frozen=True, slots=True)
class HeadToHead:
    a: str
    b: str
    a_wins: int
    b_wins: int
    ties: int
    unresolved: int


@dataclass(frozen=True, slots=True)
class PairMetrics:
    candidate: str
    brier: float
    log_loss: float
    auc: float
    calibration_error: float
    brier_skill: float
    complexity: float


@dataclass(frozen=True, slots=True)
class RoundThreeResult:
    survivors: tuple[str, ...]
    matches: tuple[HeadToHead, ...]
    ranking: tuple[tuple[str, int], ...]


def _pair_metrics(candidate: str, world) -> PairMetrics:
    spec = CandidateSpec(candidate, (candidate,))
    metrics = evaluate_candidate(spec, world.predictions[candidate], world.labels)
    return PairMetrics(
        candidate=candidate,
        brier=metrics.brier,
        log_loss=metrics.log_loss,
        auc=metrics.auc,
        calibration_error=metrics.calibration_error,
        brier_skill=metrics.brier_skill,
        complexity=metrics.complexity,
    )


def _winner_for_pair(a: str, b: str, world) -> tuple[str | None, bool]:
    """Compare two available mechanisms using the frozen evidence hierarchy."""
    if a not in world.predictions or b not in world.predictions:
        return None, True

    left = _pair_metrics(a, world)
    right = _pair_metrics(b, world)

    # Brier is primary: lower is better. If practically tied, proceed.
    if abs(left.brier - right.brier) > BRIER_TOLERANCE:
        return (a if left.brier < right.brier else b), False

    # Log loss is second: lower is better.
    if abs(left.log_loss - right.log_loss) > LOG_LOSS_TOLERANCE:
        return (a if left.log_loss < right.log_loss else b), False

    # AUC is third: higher is better.
    if abs(left.auc - right.auc) > AUC_TOLERANCE:
        return (a if left.auc > right.auc else b), False

    # Calibration is fourth: lower is better.
    if abs(left.calibration_error - right.calibration_error) > CALIBRATION_TOLERANCE:
        return (a if left.calibration_error < right.calibration_error else b), False

    # Only complexity remains. Equal complexity means a genuine tie.
    if abs(left.complexity - right.complexity) > COMPLEXITY_TOLERANCE:
        return (a if left.complexity < right.complexity else b), False

    return None, False


def run_round_three() -> RoundThreeResult:
    round2 = run_round_two()
    survivors = tuple(sorted(set(round2.survivors)))
    worlds = build_adversarial_worlds()
    wins: Counter[str] = Counter()
    matches: list[HeadToHead] = []

    for i, a in enumerate(survivors):
        for b in survivors[i + 1 :]:
            a_wins = b_wins = ties = unresolved = 0
            for world in worlds:
                winner, is_unresolved = _winner_for_pair(a, b, world)
                if is_unresolved:
                    unresolved += 1
                elif winner == a:
                    a_wins += 1
                    wins[a] += 1
                elif winner == b:
                    b_wins += 1
                    wins[b] += 1
                else:
                    ties += 1
            matches.append(HeadToHead(a, b, a_wins, b_wins, ties, unresolved))

    ranking = tuple(sorted(wins.items(), key=lambda item: (-item[1], item[0])))
    return RoundThreeResult(survivors, tuple(matches), ranking)


def render(result: RoundThreeResult | None = None) -> str:
    result = result or run_round_three()
    lines = [
        "TIAMAT TOURNAMENT ROUND 3 — HEAD TO HEAD",
        "comparison_order=Brier,LogLoss,AUC,CalibrationError,Complexity",
        f"tolerances=brier:{BRIER_TOLERANCE},log_loss:{LOG_LOSS_TOLERANCE},auc:{AUC_TOLERANCE},calibration:{CALIBRATION_TOLERANCE}",
        f"survivors={len(result.survivors)}",
    ]
    lines.extend(f"{name}: {score}" for name, score in result.ranking)
    for match in result.matches:
        lines.append(
            f"MATCH {match.a} vs {match.b}: {match.a_wins}-{match.b_wins}, "
            f"ties={match.ties}, unresolved={match.unresolved}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
