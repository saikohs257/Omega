from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .modes import TiamatMode
from .state import TiamatState
from .telemetry import TelemetryAdapter, TelemetryRow
from .transition import transition

DVQT_EXPERIMENT_VERSION = "dvqt-v1"


@dataclass(frozen=True, slots=True)
class ReducedState:
    """Minimal candidate state: damage, damage velocity, mode, mode age."""
    D: float
    V: float
    q: TiamatMode
    tau: float


@dataclass(frozen=True, slots=True)
class Disagreement:
    index: int
    timestamp: str | None
    full_q: str
    reduced_q: str
    full_transition: bool
    reduced_transition: bool
    timing_delta: int | None
    D: float
    V: float
    tau: float
    full_state: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DVQTEvaluation:
    version: str
    rows: int
    agreements: int
    disagreements: tuple[Disagreement, ...]

    @property
    def agreement_rate(self) -> float:
        return self.agreements / self.rows if self.rows else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "rows": self.rows,
            "agreements": self.agreements,
            "agreement_rate": self.agreement_rate,
            "disagreements": [item.to_dict() for item in self.disagreements],
        }


def reduce_row(row: TelemetryRow) -> ReducedState:
    """Project canonical telemetry without inventing a new threshold or mode."""
    return ReducedState(D=row.D, V=row.V, q=row.mode, tau=row.tau_mode)


def _transition_from_reduced(state: ReducedState) -> ReducedState:
    """Apply the existing transition law while exposing only D, V, q and tau."""
    reduced_state = TiamatState(
        B=0.0,
        V=state.V,
        D=state.D,
        tau_D=0.0,
        tau_mode=state.tau,
        mode=state.q,
        model_id="DVQT",
    )
    evidence = {"D": state.D, "V": state.V, "tau_mode": state.tau}
    next_state = transition(reduced_state, evidence)
    return ReducedState(next_state.D, next_state.V, next_state.mode, next_state.tau_mode)


def compare(rows: Sequence[Mapping[str, Any] | TelemetryRow], *, adapter: TelemetryAdapter | None = None) -> DVQTEvaluation:
    """Blind replay comparison against observed full-state mode transitions.

    No fitting, threshold tuning, dictionary mutation, or new modes occurs here.
    """
    adapter = adapter or TelemetryAdapter()
    normalized = tuple(adapter.normalize(row) for row in rows)
    if len(normalized) < 2:
        return DVQTEvaluation(DVQT_EXPERIMENT_VERSION, len(normalized), len(normalized), ())

    reduced = reduce_row(normalized[0])
    disagreements: list[Disagreement] = []
    agreements = 0
    last_full_transition: int | None = None
    last_reduced_transition: int | None = None

    for index, (before, observed) in enumerate(zip(normalized, normalized[1:]), start=1):
        predicted = _transition_from_reduced(reduced)
        full_transition = observed.mode is not before.mode
        reduced_transition = predicted.q is not before.mode
        if full_transition:
            last_full_transition = index
        if reduced_transition:
            last_reduced_transition = index
        if predicted.q is observed.mode:
            agreements += 1
        else:
            timing_delta = None
            if last_full_transition is not None and last_reduced_transition is not None:
                timing_delta = last_reduced_transition - last_full_transition
            disagreements.append(Disagreement(
                index=index,
                timestamp=observed.timestamp,
                full_q=observed.mode.value,
                reduced_q=predicted.q.value,
                full_transition=full_transition,
                reduced_transition=reduced_transition,
                timing_delta=timing_delta,
                D=observed.D,
                V=observed.V,
                tau=observed.tau_mode,
                full_state=observed.to_mapping(),
            ))
        reduced = reduce_row(observed)

    return DVQTEvaluation(DVQT_EXPERIMENT_VERSION, len(normalized), agreements, tuple(disagreements))
