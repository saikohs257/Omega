from __future__ import annotations
from enum import Enum


class TiamatMode(str, Enum):
    """TIAMAT semantic mode names with stable compact wire values."""

    QUIESCENT = "Q"
    PRECURSOR = "P"
    EXCITATION = "E"
    COUPLED_TRANSFER = "C"
    HAZARD = "H"
    RELAXATION = "R"
    REFRACTORY = "Rf"

    @property
    def semantic_name(self) -> str:
        """Human-readable semantic identifier; does not alter wire encoding."""
        return self.name
