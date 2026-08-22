from __future__ import annotations
from enum import Enum


class TiamatMode(str, Enum):
    """Canonical TIAMAT mode names.

    Values are the stable serialized names.  Historical compact wire tokens
    remain accepted by TiamatState._coerce_mode() for backward compatibility.
    """

    QUIESCENT = "QUIESCENT"
    PRECURSOR = "PRECURSOR"
    EXCITATION = "EXCITATION"
    COUPLED_TRANSFER = "COUPLED_TRANSFER"
    HAZARD = "HAZARD"
    RELAXATION = "RELAXATION"
    REFRACTORY = "REFRACTORY"
