"""Non-authoritative constants for the TIAMAT identification laboratory."""
from __future__ import annotations
HAZARD_BANDS: tuple[float, float, float] = (0.343, 0.599, 0.794)
DORMANCY_REFRACTORY_THRESHOLD: float = 0.95
RETIRED_FIXED_CHOKE_HOURS: None = None
STATE_CANDIDATES: tuple[tuple[str, ...], ...] = ((), ("B",), ("B", "V"), ("B", "V", "D"), ("B", "V", "D", "tau_D"), ("B", "V", "D", "tau_D", "tau_M"), ("B", "V", "D", "tau_D", "tau_M", "Phi"))

def hazard_band(value: float) -> int:
    if value < HAZARD_BANDS[0]: return 0
    if value < HAZARD_BANDS[1]: return 1
    if value < HAZARD_BANDS[2]: return 2
    return 3
