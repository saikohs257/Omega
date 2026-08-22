from __future__ import annotations
from enum import Enum


class TiamatMode(str, Enum):
    """Canonical TIAMAT mode names with stable compact wire values.

    The enum member names are the semantic identifiers. The values are the
    established serialized/wire tokens used by existing telemetry, tests,
    and transition ledgers. Historical long-form names are accepted by
    TiamatState._coerce_mode().
    """

    QUIESCENT = "Q"
    PRECURSOR = "P"
    EXCITATION = "E"
    COUPLED_TRANSFER = "C"
    HAZARD = "H"
    RELAXATION = "R"
    REFRACTORY = "Rf"
