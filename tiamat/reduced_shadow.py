"""Minimal TIAMAT shadow for blind state-sufficiency experiments.

This module is deliberately conservative.  It does not reimplement the full
TIAMAT state or import candidate explanatory variables.  The shadow carries
only D, V, q and tau_mode.  Other observables are retained only in the replay
ledger, never in the shadow decision.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Mapping

from .modes import TiamatMode
from .state import TiamatState
from .transition import LEGAL


@dataclass(frozen=True, slots=True)
class ReducedState:
    D: float = 0.0
    V: float = 0.0
    q: TiamatMode = TiamatMode.QUIESCENT
    tau: float = 0.0


@dataclass(frozen=True, slots=True)
class ReducedShadow:
    """State machine constrained to D,V,q,tau.

    The shadow intentionally has no B/Phi/recovery/residual-load/coupling
    inputs.  Its transition rules reuse only legal mode topology and the
    existing D/V-based transition semantics; they do not inspect the full
    telemetry row.
    """

    def step(self, state: ReducedState, row: Mapping[str, Any]) -> ReducedState:
        d = float(row.get("D", state.D))
        v = float(row.get("V", state.V))
        q = state.q
        tau = state.tau + 1.0

        if q is TiamatMode.QUIESCENT and v > 0:
            target = TiamatMode.PRECURSOR
        elif q is TiamatMode.PRECURSOR and v <= 0:
            target = TiamatMode.QUIESCENT
        elif q is TiamatMode.EXCITATION and v < 0:
            target = TiamatMode.RELAXATION
        elif q is TiamatMode.COUPLED_TRANSFER and v < 0:
            target = TiamatMode.RELAXATION
        elif q is TiamatMode.HAZARD and v < 0:
            target = TiamatMode.RELAXATION
        elif q is TiamatMode.RELAXATION and d <= 0.0 and v >= 0:
            target = TiamatMode.QUIESCENT
        elif q is TiamatMode.REFRACTORY and d <= 0.0 and v >= 0:
            target = TiamatMode.QUIESCENT
        else:
            target = q

        if target is not q and target not in LEGAL.get(q, set()):
            target = q
        if target is not q:
            tau = 0.0
        return ReducedState(D=d, V=v, q=target, tau=tau)

    def from_row(self, row: Mapping[str, Any]) -> ReducedState:
        mode = row.get("mode", TiamatMode.QUIESCENT)
        if not isinstance(mode, TiamatMode):
            mode = TiamatMode(str(mode))
        return ReducedState(
            D=float(row.get("D", 0.0)),
            V=float(row.get("V", 0.0)),
            q=mode,
            tau=float(row.get("tau_mode", 0.0)),
        )
