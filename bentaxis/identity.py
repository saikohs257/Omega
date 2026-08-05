from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def to_canonical_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=repr).encode("utf-8")


@dataclass(frozen=True, slots=True)
class Identity:
    digest: str

    @classmethod
    def calculate(cls, obj: Any) -> "Identity":
        return cls(hashlib.sha256(to_canonical_bytes(obj)).hexdigest())
