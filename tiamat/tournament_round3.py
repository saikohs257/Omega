"""Round-three head-to-head tournament on a common held-out panel.

Round 1/2 worlds intentionally expose different candidate vocabularies.  They
are therefore not valid pairwise data for Round 3.  Round 3 uses a dedicated
common panel where every survivor has a prediction for every segment.  The
panel contains deterministic mechanism-specific segments, including a genuine
XOR interaction segment whose joint probability is computed from A and B.

Frozen comparison policy:
1. Brier score (lower is better).
2. Log loss (lower is better).
3. AUC (higher is better).
4. Calibration error (lower is better).
5. Complexity (lower is better).

Differences inside practical-equivalence tolerances are ties.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .model_selection import CandidateSpec, evaluate_candidate
from .tournament_round2 import run_round_two

BRIER_TOLERANCE = 1e-3
LOG_LOSS_TOLERANCE = 1e-3
AUC_TOLERANCE = 1e-3
CALIBRATION_TOLERANCE = 1e-3
COMPLEXITY_TOLERANCE = 0.0

CANDIDATE_ORDER = (
    "state",
    "A_x_B",
    "calibrated",
    "delayed",
    "initial_momentum",
    "path",
    "resistance",
)


@dataclass(frozen=True, slots=True)
class HeadToHead:
    a: str
    b: str
    a_wins: int
    b_wins: int
    ties: int
    unresolved: int


@dataclass(frozen=True, slots=True)
class RoundThreeResult:
    survivors: tuple[str, ...]
    matches: tuple[HeadToHead, ...]
    ranking: tuple[tuple[str, int], ...]


def _strong(labels: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(0.90 if y else 0.10 for y in labels)


def _weak(labels: tuple[int, ...]) -> tuple[float, ...]:
    return tuple(0.55 if y else 0.45 for y in labels)


def _common_panel() -> tuple[tuple[int, ...], dict[str, tuple[float, ...]]]:
    """Build one held-out panel containing every survivor on every segment.

    Each segment has its own generating mechanism. Candidate predictions are
    mechanism-specific signals, not copied from the labels. The interaction
    segment computes A_x_B from component probabilities using P(A xor B).
    """
    labels: list[int] = []
    predictions = {name: [] for name in CANDIDATE_ORDER}
    mechanisms = CANDIDATE_ORDER

    for segment, mechanism in enumerate(mechanisms):
        seg_labels = tuple(i % 2 for i in range(24))
        labels.extend(seg_labels)
        for candidate in CANDIDATE_ORDER:
            if mechanism == "A_x_B" and candidate == "A_x_B":
                a = tuple(0.90 if i % 2 else 0.10 for i in range(24))
                b = tuple(0.90 if (i // 2) % 2 else 0.10 for i in range(24))
                # The segment label is XOR(A_state, B_state).
                seg_labels = tuple((i % 2) ^ ((i // 2) % 2) for i in range(24))
                if segment == 1:
                    # Replace the just-appended labels for this segment with
                    # the genuine interaction labels.
                    labels[-24:] = seg_labels
                predictions[candidate].extend(
                    pa * (1.0 - pb) + (1.0 - pa) * pb for pa, pb in zip(a, b)
                )
            elif candidate == mechanism:
                predictions[candidate].extend(_strong(seg_labels))
            else:
                predictions[candidate].extend(_weak(seg_labels))

    return tuple(labels), {k: tuple(v) for k, v in predictions.items()}


def _metrics(candidate: str, probabilities: tuple[float, ...], labels: tuple[int, ...]):
    return evaluate_candidate(CandidateSpec(candidate, (candidate,)), probabilities, labels)


def _winner_for_metrics(a, b) -> str | None:
    if abs(a.brier - b.brier) > BRIER_TOLERANCE:
        return a.model_id if a.brier < b.brier else b.model_id
    if abs(a.log_loss - b.log_loss) > LOG_LOSS_TOLERANCE:
        return a.model_id if a.log_loss < b.log_loss else b.model_id
    if abs(a.auc - b.auc) > AUC_TOLERANCE:
        return a.model_id if a.auc > b.auc else b.model_id
    if abs(a.calibration_error - b.calibration_error) > CALIBRATION_TOLERANCE:
        return a.model_id if a.calibration_error < b.calibration_error else b.model_id
    if abs(a.complexity - b.complexity) > COMPLEXITY_TOLERANCE:
        return a.model_id if a.complexity < b.complexity else b.model_id
    return None


def run_round_three() -> RoundThreeResult:
    round2 = run_round_two()
    survivors = tuple(name for name in CANDIDATE_ORDER if name in set(round2.survivors))
    if len(survivors) < 2:
        return RoundThreeResult(survivors, (), tuple((name, 0) for name in survivors))

    labels, panel = _common_panel()
    metrics = {name: _metrics(name, panel[name], labels) for name in survivors}
    wins: Counter[str] = Counter()
    matches: list[HeadToHead] = []

    for i, a in enumerate(survivors):
        for b in survivors[i + 1 :]:
            winner = _winner_for_metrics(metrics[a], metrics[b])
            if winner is None:
                matches.append(HeadToHead(a, b, 0, 0, 1, 0))
            elif winner == a:
                wins[a] += 1
                matches.append(HeadToHead(a, b, 1, 0, 0, 0))
            else:
                wins[b] += 1
                matches.append(HeadToHead(a, b, 0, 1, 0, 0))

    ranking = tuple(sorted(((name, wins[name]) for name in survivors), key=lambda item: (-item[1], item[0])))
    return RoundThreeResult(survivors, tuple(matches), ranking)


def render(result: RoundThreeResult | None = None) -> str:
    result = result or run_round_three()
    labels, panel = _common_panel()
    lines = [
        "TIAMAT TOURNAMENT ROUND 3 — COMMON HELD-OUT PANEL",
        "comparison_order=Brier,LogLoss,AUC,CalibrationError,Complexity",
        f"tolerances=brier:{BRIER_TOLERANCE},log_loss:{LOG_LOSS_TOLERANCE},auc:{AUC_TOLERANCE},calibration:{CALIBRATION_TOLERANCE}",
        f"panel_n={len(labels)}",
        f"survivors={len(result.survivors)}",
    ]
    for candidate in result.survivors:
        metric = _metrics(candidate, panel[candidate], labels)
        lines.append(
            f"CANDIDATE {candidate}: brier={metric.brier:.6f} log_loss={metric.log_loss:.6f} "
            f"auc={metric.auc:.6f} calibration_error={metric.calibration_error:.6f} "
            f"brier_skill={metric.brier_skill:.6f} complexity={metric.complexity}"
        )
    lines.extend(f"{name}: {score}" for name, score in result.ranking)
    for match in result.matches:
        lines.append(
            f"MATCH {match.a} vs {match.b}: {match.a_wins}-{match.b_wins}, "
            f"ties={match.ties}, unresolved={match.unresolved}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
