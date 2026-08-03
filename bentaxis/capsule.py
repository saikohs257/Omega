from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import to_canonical_bytes
from bentaxis.store import BentAxisStore


@dataclass(frozen=True, slots=True)
class BentAxisCapsule:
    manifest: Mapping[str, Any]
    payload: bytes

    def bytes(self) -> bytes:
        return self.payload

    def text(self) -> str:
        return self.payload.decode("utf-8")

    @classmethod
    def from_store(cls, store: BentAxisStore) -> BentAxisCapsule:
        manifest = {
            "count": len(store.events),
            "chain_head": store.chain.head,
            "digests": [record.identity.digest for record in store.events],
        }
        payload_obj = {
            "manifest": manifest,
            "events": [
                {
                    "identity": record.identity.digest,
                    "kind": record.event.kind,
                    "payload": record.event.payload,
                    "metadata": record.event.metadata,
                }
                for record in store.events
            ],
        }
        payload = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return cls(manifest=manifest, payload=payload)

    def canonical_hash(self) -> str:
        import hashlib

        return hashlib.sha256(to_canonical_bytes({"manifest": dict(self.manifest), "payload": self.payload})).hexdigest()
