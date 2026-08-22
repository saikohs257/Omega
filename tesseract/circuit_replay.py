from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.constitutional_record import ConstitutionalRecord
from runtime.state_vector import StateVector


RECORD_TYPE = "TESSERACT_CIRCUIT_TRACE"


@dataclass(frozen=True, slots=True)
class CircuitTraceReplayOperator:
    """Deterministic reconstruction operator for a circuit trace record."""

    def reconstruct(self, record: ConstitutionalRecord, state: StateVector) -> StateVector:
        if record.record_type != RECORD_TYPE:
            raise ValueError(f"unsupported record type: {record.record_type}")
        payload = dict(record.payload)
        row = dict(payload.get("row", {}))
        if row.get("runtime_allowed", False):
            raise ValueError("replay cannot reconstruct runtime-authorized circuit traces")
        return state.with_updates(
            record_count=state.get("record_count", 0) + 1,
            last_record_type=record.record_type,
            last_record_id=record.record_id,
            tesseract_circuit_row=row,
            tesseract_circuit_identity=payload.get("row_identity", ""),
        )


def register_circuit_trace(registry: Any) -> None:
    registry.register(RECORD_TYPE, CircuitTraceReplayOperator())
