"""Head-to-head tournament for candidates surviving Round 2."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .adversarial_worlds import build_adversarial_worlds
from .model_selection import CandidateSpec
from .tournament import TournamentCase, TournamentRunner
from .tournament_round2 import run_round_two


@dataclass(frozen=True, slots=True)
class HeadToHead:
    a: str
    b: str
    a_wins: int
    b_wins: int
    ties: int


@dataclass(frozen=True, slots=True)
class RoundThreeResult:
    survivors: tuple[str, ...]
    matches: tuple[HeadToHead, ...]
    ranking: tuple[tuple[str, int], ...]


def run_round_three() -> RoundThreeResult:
    round2 = run_round_two()
    survivors = tuple(sorted(set(round2.survivors)))
    worlds = build_adversarial_worlds()
    wins: Counter[str] = Counter()
    matches: list[HeadToHead] = []

    for i, a in enumerate(survivors):
        for b in survivors[i + 1 :]:
            a_wins = b_wins = ties = 0
            for world in worlds:
                available = {a, b} & set(world.predictions)
                if len(available) < 2:
                    continue
                specs = tuple(CandidateSpec(name, (name,)) for name in (a, b))
                result = TournamentRunner(specs=specs).run_case(
                    TournamentCase(
                        name=f"h2h:{world.name}:{a}:{b}",
                        labels=world.labels,
                        heldout_predictions={name: world.predictions[name] for name in (a, b)},
                        max_size=2,
                        specs=specs,
                    )
                )
                winner = result.decision.selected_model_id
                if winner == a:
                    a_wins += 1
                    wins[a] += 1
                elif winner == b:
                    b_wins += 1
                    wins[b] += 1
                else:
                    ties += 1
            matches.append(HeadToHead(a, b, a_wins, b_wins, ties))

    ranking = tuple(sorted(wins.items(), key=lambda item: (-item[1], item[0])))
    return RoundThreeResult(survivors, tuple(matches), ranking)


def render(result: RoundThreeResult | None = None) -> str:
    result = result or run_round_three()
    lines = ["TIAMAT TOURNAMENT ROUND 3 — HEAD TO HEAD", f"survivors={len(result.survivors)}"]
    lines.extend(f"{name}: {score}" for name, score in result.ranking)
    for match in result.matches:
        lines.append(f"MATCH {match.a} vs {match.b}: {match.a_wins}-{match.b_wins}, ties={match.ties}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render())
