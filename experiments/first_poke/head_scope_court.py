"""Scoped TIAMAT head court.

This is deliberately an experiment, not an authority implementation.
It tests whether the canonical transition topology can be evaluated without
silently broadening a head's legal domain.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

HEADS = {
    "H0": ("Q", "R"),
    "H2": ("E", "R"),
    "H3": ("C", "R"),
    "H4": ("H", "H"),
    "ExitBridge": ("R", "Rf"),
}


@dataclass(frozen=True)
class HeadResult:
    head: str
    legal_hits: int
    illegal_hits: int
    legal_target_hits: int
    contamination_hits: int


def evaluate(transitions: list[tuple[str, str]]) -> list[HeadResult]:
    out = []
    for head, (src, dst) in HEADS.items():
        legal = sum(a == src and b == dst for a, b in transitions)
        illegal = sum(a == src and b != dst for a, b in transitions)
        target = sum(b == dst for _, b in transitions)
        contamination = target - legal
        out.append(HeadResult(head, legal, illegal, target, contamination))
    return out


def main() -> None:
    # Synthetic topology sanity court only. Historical evidence is supplied
    # by the real Layer-1 replay; this fixture does not claim performance.
    transitions = [
        ("Q", "R"), ("E", "R"), ("C", "R"), ("H", "H"), ("R", "Rf"),
        ("Q", "P"), ("E", "P"), ("C", "H"), ("H", "R"), ("R", "H"),
    ]
    results = evaluate(transitions)
    for r in results:
        print(f"{r.head}: legal={r.legal_hits} illegal={r.illegal_hits} "
              f"target={r.legal_target_hits} contamination={r.contamination_hits}")
    assert all(r.legal_hits == 1 for r in results)
    assert all(r.contamination_hits >= 0 for r in results)


if __name__ == "__main__":
    main()
