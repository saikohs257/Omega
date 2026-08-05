from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Mapping

_CANONICAL_VERSION = "identity-v2"


def _normalize(obj: Any) -> Any:
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        if obj != obj:
            return {"$float": "nan"}
        if obj == float("inf"):
            return {"$float": "inf"}
        if obj == float("-inf"):
            return {"$float": "-inf"}
        return {"$float": format(obj, ".17g")}
    if isinstance(obj, Decimal):
        return {"$decimal": format(obj, "f")}
    if isinstance(obj, bytes):
        return {"$bytes": obj.hex()}
    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=timezone.utc)
        return {"$datetime": obj.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")}
    if isinstance(obj, date) and not isinstance(obj, datetime):
        return {"$date": obj.isoformat()}
    if isinstance(obj, time):
        return {"$time": obj.isoformat()}
    if dataclasses.is_dataclass(obj):
        return {
            "$dataclass": obj.__class__.__qualname__,
            "fields": [[field.name, _normalize(getattr(obj, field.name))] for field in dataclasses.fields(obj)],
        }
    if isinstance(obj, Mapping):
        return {str(key): _normalize(value) for key, value in sorted(obj.items(), key=lambda item: str(item[0]))}
    if isinstance(obj, tuple):
        return ["$tuple", [_normalize(value) for value in obj]]
    if isinstance(obj, list):
        return [_normalize(value) for value in obj]
    if isinstance(obj, (set, frozenset)):
        normalized = [_normalize(value) for value in obj]
        return {"$set": sorted(normalized, key=lambda value: json.dumps(value, sort_keys=True, separators=(",", ":")))}
    if hasattr(obj, "__canonical__"):
        return _normalize(obj.__canonical__())
    if hasattr(obj, "__dict__"):
        return {
            "$object": obj.__class__.__qualname__,
            "state": _normalize(vars(obj)),
        }
    return {"$repr": repr(obj)}


def to_canonical_bytes(obj: Any) -> bytes:
    payload = {
        "version": _CANONICAL_VERSION,
        "data": _normalize(obj),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(frozen=True, slots=True)
class Identity:
    digest: str
    canonical_payload: Any | None = None

    @classmethod
    def calculate(cls, obj: Any) -> "Identity":
        canonical_payload = _normalize(obj)
        digest = hashlib.sha256(
            to_canonical_bytes(canonical_payload)
        ).hexdigest()
        return cls(digest=digest, canonical_payload=canonical_payload)
