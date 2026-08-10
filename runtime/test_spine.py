from __future__ import annotations

from dataclasses import dataclass


class TestSpineViolation(PermissionError):
    """Raised when adaptive components attempt to access the locked test spine."""


@dataclass(frozen=True, slots=True)
class TestSpine:
    spine_id: str
    locked: bool = True

    def read(self, requester: str) -> None:
        if self.locked and requester in {"end", "pond", "oracle_mutation", "diagnostic_tuner"}:
            raise TestSpineViolation(f"{requester} cannot access locked test spine {self.spine_id}")
        return None
