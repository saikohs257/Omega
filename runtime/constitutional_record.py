from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from bentaxis.identity import Identity, to_canonical_bytes


@dataclass(frozen=True, slots=True)
class ConstitutionalRecord:
    """Immutable constitutional history record.

    This is the kernel ABI record primitive. It is intentionally boring:
    it carries canonical payload, provenance, identity references, and
    append-only linkage, but no reconstruction logic.
    """

    record_type: str
    payload: Mapping[str, Any]
    identity_refs: tuple[str, ...] = field(default_factory=tuple)
    jurisdiction: str = ""
    provenance: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    previous_record: str = ""
    schema_version: str = "constitutional-record-v1"
    signature: str = ""
    timestamp: str = ""
    record_id: str = field(init=False)

    def __post_init__(self) -> None:
        canonical = to_canonical_bytes(
            {
                "record_type": self.record_type,
                "payload": dict(self.payload),
                "identity_refs": self.identity_refs,
                "jurisdiction": self.jurisdiction,
                "provenance": self.provenance,
                "previous_record": self.previous_record,
                "schema_version": self.schema_version,
                "signature": self.signature,
                "timestamp": self.timestamp,
            }
        )
        object.__setattr__(self, "record_id", Identity.calculate(canonical).digest)

    @property
    def canonical_payload(self) -> dict[str, Any]:
        return {
            "record_type": self.record_type,
            "payload": dict(self.payload),
            "identity_refs": self.identity_refs,
            "jurisdiction": self.jurisdiction,
            "provenance": self.provenance,
            "previous_record": self.previous_record,
            "schema_version": self.schema_version,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }
