from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class AtlasNeighborhood:
    origin: tuple[int, ...]
    neighbors: tuple[tuple[int, ...], ...]


class Atlas(Protocol):
    def project(self, state: Any) -> tuple[int, ...]:
        ...

    def distance(self, left: tuple[int, ...], right: tuple[int, ...]) -> int:
        ...

    def local_chart(self, coordinate: tuple[int, ...]) -> AtlasNeighborhood:
        ...

    def get_neighbors(self, coordinate: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
        ...
