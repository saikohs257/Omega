from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .experiment_manifest import corpus_fingerprint


@dataclass(frozen=True, slots=True)
class CorpusSnapshot:
    """Immutable in-process snapshot of the exact corpus used by an experiment."""

    rows: tuple[dict[str, Any], ...]
    manifest_hash: str

    @classmethod
    def freeze(cls, rows: Sequence[Mapping[str, Any]]) -> "CorpusSnapshot":
        frozen = tuple(dict(row) for row in rows)
        if not frozen:
            raise ValueError("cannot freeze an empty corpus")
        manifest_hash = corpus_fingerprint(frozen)
        return cls(frozen, manifest_hash)

    def verify(self) -> None:
        current = corpus_fingerprint(self.rows)
        if current != self.manifest_hash:
            raise ValueError("frozen corpus snapshot has changed")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "corpus-snapshot-v1",
            "manifest_hash": self.manifest_hash,
            "row_count": len(self.rows),
            "rows": [dict(row) for row in self.rows],
        }
