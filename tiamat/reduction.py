"""Minimal-state reduction shadow replay.

This module is deliberately observational. It does not alter TIAMAT guards,
thresholds, modes, or the production transition function. It creates a blind
shadow representation using only D, V, current mode (q), and mode age (tau),
then compares that representation with the canonical replay.

The purpose is falsification: disagreements are evidence to investigate, not
permission to add another state variable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .state import TiamatState
from .telemetry import TelemetryAdapter, TelemetryRow
from .transition import transition


@dataclass(frozen=True, slots=True)
class ReducedState:
    """The smallest proposed state: D, V, q, and mode age."""

    D: float
    V: float
    q: str
    tau: float

    @classmethod
    def from_state(cls, state: TiamatState) -> "ReducedState":
        return cls(D=state.D, V=state.V, q=state.mode.value, tau=state.tau_mode)

    def to_dict(self) -> dict[str, Any]:
        return {"D": self.D, "V": self.V, "q": self.q, "tau": self.tau}


@dataclass(frozen=True, slots=True)
class DisagreementRecord:
    """One row of the blind full-vs-reduced comparison ledger."""

    index: int
    timestamp: str | None
    full_q: str
    reduced_q: str
    full_transition: str | None
    reduced_transition: str | None
    timing_delta: int | None
    D: float
    V: float
    tau: float

    @property
    def agreement(self) -> bool:
        return self.full_q == self.reduced_q and self.full_transition == self.reduced_transition

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "full_q": self.full_q,
            "reduced_q": self.reduced_q,
            "full_transition": self.full_transition,
            "reduced_transition": self.reduced_transition,
            "timing_delta": self.timing_delta,
            "D": self.D,
            "V": self.V,
            "tau": self.tau,
            "agreement": self.agreement,
        }


@dataclass(frozen=True, slots=True)
class ReductionReplay:
    """Result of replaying an observed spine through the shadow ledger."""

    rows: tuple[DisagreementRecord, ...]

    @property
    def disagreements(self) -> tuple[DisagreementRecord, ...]:
        return tuple(row for row in self.rows if not row.agreement)

    @property
    def agreement_rate(self) -> float:
        return sum(row.agreement for row in self.rows) / len(self.rows) if self.rows else 1.0


def reduced_state(state: TiamatState) -> ReducedState:
    return ReducedState.from_state(state)


def replay_shadow(
    rows: Sequence[Mapping[str, Any] | TelemetryRow],
    *,
    adapter: TelemetryAdapter | None = None,
) -> ReductionReplay:
    """Build the blind D,V,q,tau ledger from an observed telemetry spine.

    The reduced shadow is intentionally not allowed to invent a transition
    rule. The canonical transition supplies the observed/full trajectory;
    reduced_q is the mode attached to the same observation. This first phase
    therefore measures representation sufficiency and creates the forensic
    ledger before any reduced transition model is fitted.
    """
    adapter = adapter or TelemetryAdapter()
    normalized = tuple(adapter.normalize(row) for row in rows)
    records: list[DisagreementRecord] = []
    for index, row in enumerate(normalized):
        state = row.to_state()
        previous = normalized[index - 1].mode.value if index else None
        current = state.mode.value
        full_transition = None if previous is None or previous == current else f"{previous}->{current}"
        reduced = ReducedState.from_state(state)
        records.append(
            DisagreementRecord(
                index=index,
                timestamp=row.timestamp,
                full_q=current,
                reduced_q=reduced.q,
                full_transition=full_transition,
                reduced_transition=full_transition,
                timing_delta=0 if full_transition is not None else None,
                D=reduced.D,
                V=reduced.V,
                tau=reduced.tau,
            )
        )
    return ReductionReplay(tuple(records))


def replay_transition_shadow(
    initial: TiamatState,
    evidence: Sequence[Mapping[str, Any]],
) -> tuple[ReducedState, ...]:
    """Replay canonical transitions while exposing only the reduced state.

    This is a diagnostic bridge, not a reduced predictor: production
    transition semantics remain the control. It is useful for verifying that
    the proposed D,V,q,tau projection is lossless before fitting a new model.
    """
    state = initial
    out: list[ReducedState] = []
    for row in evidence:
        state = transition(state, row)
        out.append(ReducedState.from_state(state))
    return tuple(out)
