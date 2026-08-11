"""World-conditioned component selection for generic synthetic experiments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .world_library import COMPONENT_DICTIONARY, MechanismProfile


@dataclass(frozen=True, slots=True)
class Selection:
    component: str
    compatibility: float
    matched_mechanisms: tuple[str, ...]


def rank_candidates(mechanisms: Iterable[str], *, limit: int | None = None) -> tuple[Selection, ...]:
    """Rank candidates by capability/requirement compatibility.

    This is deliberately a prior, not a prediction result.  It must be followed
    by empirical evaluation on the selected world's held-out observations.
    """
    observed = set(mechanisms)
    ranked: list[Selection] = []
    for name, profile in COMPONENT_DICTIONARY.items():
        matches = tuple(sorted(set(profile.detects) & observed))
        required_hits = len(set(profile.requires) & observed)
        compatibility = 2.0 * len(matches) + 0.5 * required_hits
        if matches:
            ranked.append(Selection(name, compatibility, matches))
    ranked.sort(key=lambda item: (-item.compatibility, item.component))
    return tuple(ranked[:limit] if limit is not None else ranked)
