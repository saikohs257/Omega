"""HYDRA: compartmentalized, upgradeable TIAMAT successor architecture.

HYDRA deliberately does not replace ``tiamat``.  TIAMAT remains the reference
implementation used for differential/conformance experiments.  HYDRA exposes
independent state engines behind a shared, immutable state bus and a coordinator
that preserves module disagreement instead of collapsing it prematurely.
"""

from .state import HydraEvidence, HydraState, HydraDecision
from .engine import HydraEngine

__all__ = [
    "HydraEvidence",
    "HydraState",
    "HydraDecision",
    "HydraEngine",
]
