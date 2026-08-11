"""Blind replay comparison ledger for the minimal-state experiment."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .reduced_shadow import ReducedShadow, ReducedState
from .state import TiamatState
from .telemetry import TelemetryAdapter, TelemetryRow
from .transition import transition


@dataclass(frozen=True, slots=True)
class DisagreementRecord:
    transition_id: int
    timestamp: str | None
    episode_id: str | None
    full_q: str
    reduced_q: str
    full_transition: bool
    reduced_transition: bool
    full_decision: str
    reduced_decision: str
    timing_delta: int | None
    D: float
    V: float
    tau: float
    full_state_snapshot: dict[str, Any]
    reduced_state_snapshot: dict[str, Any]
    candidate_residuals: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ReplayReport:
    records: tuple[DisagreementRecord, ...]
    rows: int
    disagreements: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": "reduced-v1",
            "rows": self.rows,
            "disagreements": self.disagreements,
            "records": [asdict(record) for record in self.records],
        }


def blind_replay(rows: Sequence[Mapping[str, Any] | TelemetryRow]) -> ReplayReport:
    """Replay identical rows through Full and Reduced without fitting.

    The reduced side receives only D, V and its own q/tau state.  Full TIAMAT
    receives the complete canonical row.  No residual analysis occurs here.
    """
    adapter = TelemetryAdapter()
    normalized = tuple(adapter.normalize(row) for row in rows)
    if not normalized:
        return ReplayReport((), 0, 0)

    shadow = ReducedShadow()
    reduced = shadow.from_row(normalized[0].to_mapping())
    full = normalized[0].to_state()
    records: list[DisagreementRecord] = []

    previous_full_q = full.mode
    previous_reduced_q = reduced.q
    for index, row in enumerate(normalized[1:], start=1):
        full_next = transition(full, row.to_mapping())
        reduced_next = shadow.step(reduced, {"D": row.D, "V": row.V})
        full_changed = full_next.mode is not previous_full_q
        reduced_changed = reduced_next.q is not previous_reduced_q
        disagreement = full_next.mode is not reduced_next.q or full_changed != reduced_changed
        if disagreement:
            records.append(
                DisagreementRecord(
                    transition_id=index,
                    timestamp=row.timestamp,
                    episode_id=row.extras.get("episode_id"),
                    full_q=full_next.mode.value,
                    reduced_q=reduced_next.q.value,
                    full_transition=full_changed,
                    reduced_transition=reduced_changed,
                    full_decision=full_next.mode.value,
                    reduced_decision=reduced_next.q.value,
                    timing_delta=None,
                    D=row.D,
                    V=row.V,
                    tau=reduced_next.tau,
                    full_state_snapshot=full_next.to_dict(),
                    reduced_state_snapshot={
                        "D": reduced_next.D,
                        "V": reduced_next.V,
                        "q": reduced_next.q.value,
                        "tau": reduced_next.tau,
                    },
                    candidate_residuals={
                        key: value
                        for key, value in row.extras.items()
                        if key not in {"episode_id"}
                    },
                )
            )
        full = full_next
        reduced = reduced_next
        previous_full_q = full.mode
        previous_reduced_q = reduced.q

    return ReplayReport(tuple(records), len(normalized), len(records))
