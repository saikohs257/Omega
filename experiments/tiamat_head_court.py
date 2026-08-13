"""Scoped TIAMAT head court.

This is deliberately an evidence harness, not a new TIAMAT implementation.
It tests whether the canonical head scopes can be distinguished by topology,
using the recovered seven-mode state machine. No outcome labels are used to
fit a head here.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

MODES = ("Q", "P", "E", "C", "H", "R", "Rf")
HEAD_SCOPE = {
    "H0": ("Q", "R"),
    "H2": ("E", "R"),
    "H3": ("C", "R"),
    "H4": ("H", "H"),
    "ExitBridge": ("R", "Rf"),
    "PriorCarry": MODES,
}

@dataclass(frozen=True)
class Trial:
    head: str
    legal: int
    illegal: int


def score_scope(head: str) -> Trial:
    scope = HEAD_SCOPE[head]
    legal = sum(1 for a in MODES for b in MODES if (a, b) == scope)
    # Count all non-matching ordered transitions as negative controls.
    illegal = len(MODES) ** 2 - legal
    return Trial(head, legal, illegal)


def main() -> None:
    print("TIAMAT SCOPED HEAD COURT")
    print("No fitting; no outcome labels; topology-only control.")
    for head in HEAD_SCOPE:
        t = score_scope(head)
        print(f"{head}: legal={t.legal} illegal_controls={t.illegal}")
    print("pairwise scopes:")
    for a, b in combinations(HEAD_SCOPE, 2):
        print(f"{a} vs {b}: distinct={HEAD_SCOPE[a] != HEAD_SCOPE[b]}")
    print("diagnostic-only: T3, S2")


if __name__ == "__main__":
    main()
