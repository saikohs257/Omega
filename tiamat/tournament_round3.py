"""Head-to-head tournament for candidates surviving Round 2."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .adversarial_worlds import build_adversarial_worlds
from .model_selection import CandidateSpec, evaluate_candidate
from .tournament_round2 import run_round_two


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


def _winner_for_pair(a: str, b: str, world) -> tuple[str | None, bool]:
    """Score both candidates directly on the same world.

    Returns (winner, unresolved). This deliberately bypasses the tournament
    selector: the selector is allowed to return UNRESOLVED when a single model
    does not clear absolute evidence gates, but a head-to-head round asks a
    different question — which of two available mechanisms scores better on
    identical held-out evidence.
    """
    if a not in world.predictions or b not in world.predictions:
        return None, True
    specs = (
        CandidateSpec(a, (a,)),
        CandidateSpec(b, (b,)),
    )
    metrics_a = evaluate_candidate(specs[0], world.predictions[a], world.labels)
    metrics_b = evaluate_candidate(specs[1], world.predictions[b], world.labels)
    key_a = (metrics_a.score, metrics_a.auc, metrics_a.brier_skill, -metrics_a.brier, -metrics_a.log_loss, -metrics_a.complexity)
    key_b = (metrics_b.score, metrics_b.auc, metrics_b.brier_skill, -metrics_b.brier, -metrics_b.log_loss, -metrics_b.complexity)
    if key_a > key_b:
        return a, False
    if key_b > key_a:
        return b, False
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
    lines = ["TIAMAT TOURNAMENT ROUND 3 — HEAD TO HEAD", f"survivors={len(result.survivors)}"]
    lines.extend(f"{name}: {score}" for name, score in result.ranking)
    for match in result.matches:
        lines.append(
            f"MATCH {match.a} vs {match.b}: {match.a_wins}-{match.b_wins}, "
            f"ties={match.ties}, unresolved={match.unresolved}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
