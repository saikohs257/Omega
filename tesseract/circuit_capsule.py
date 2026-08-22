from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.capsule import BentAxisCapsule
from bentaxis.identity import Identity
from bentaxis.store import BentAxisStore
from runtime.constitutional_record import ConstitutionalRecord
from runtime.events import Event
from tesseract.strict_circuit import StrictCircuitRow, assert_reference_authority


@dataclass(frozen=True, slots=True)
class CircuitTraceCapsule:
    """Canonical BentAxis-facing representation of one strict circuit row."""

    row: StrictCircuitRow
    identity: Identity

    @classmethod
    def from_row(cls, row: StrictCircuitRow) -> "CircuitTraceCapsule":
        assert_reference_authority(row)
        identity = Identity.calculate(row.canonical_payload)
        return cls(row=row, identity=identity)

    @property
    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": "tesseract-circuit-trace-capsule-v1",
            "row": self.row.canonical_payload,
            "row_identity": self.identity.digest,
        }

    def to_event(self) -> Event:
        return Event.create(
            "TESSERACT_CIRCUIT_TRACE",
            payload=self.canonical_payload,
            metadata={"authority_state": self.row.authority_state, "runtime_allowed": False},
        )

    def to_constitutional_record(self, *, previous_record: str = "") -> ConstitutionalRecord:
        event = self.to_event()
        return ConstitutionalRecord(
            record_type=event.kind,
            payload=event.payload_dict(),
            identity_refs=(self.identity.digest,),
            jurisdiction="TESSERACT_CIRCUIT",
            provenance=(("source", "Q4/V1.1-hand-built"), ("authority", self.row.authority_state)),
            previous_record=previous_record,
        )

    def append_to(self, store: BentAxisStore):
        return store.append(self.to_event())

    def bentaxis_snapshot(self, store: BentAxisStore) -> BentAxisCapsule:
        self.append_to(store)
        return BentAxisCapsule.from_store(store)
