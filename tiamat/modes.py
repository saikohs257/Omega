from __future__ import annotations
from enum import Enum


class TiamatMode(str, Enum):
    QUIESCENT = "Q"
    PRECURSOR = "P"
    EXCITATION = "E"
    COUPLED_TRANSFER = "C"
    HAZARD = "H"
    RELAXATION = "R"
    REFRACTORY = "Rf"
