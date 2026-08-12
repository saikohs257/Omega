from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import re
from typing import Any, Sequence

from .experiment_manifest import canonical_hash

HF10_VERSION = "hf10-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TIMING_SEATS = ("BASE", "HOT", "PREC")
CLAIM_STATUSES = ("PASS", "FAIL", "INCOMPARABLE", "ABSTAIN", "UNRESOLVED")


def _require_hash(name: str, value: str) -> None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase 64-character SHA-256 hex digest")


def _require_non_negative_delta(name: str, value: timedelta) -> None:
    seconds = float(value.total_seconds())
    if not seconds >= 0.0 or not seconds < float("inf"):
        raise ValueError(f"{name} must be finite and non-negative")


def _format_dt(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class InformationSet:
    timing_seat: str
    observation_cutoff: datetime
    allowed_lookback: timedelta
    forbidden_future_window: timedelta
    label_offset: timedelta
    feature_snapshot_hash: str
    provenance_hash: str
    corpus_manifest_hash: str
    registry_snapshot_hash: str
    information_set_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.timing_seat not in TIMING_SEATS:
            raise ValueError(f"timing_seat must be one of {TIMING_SEATS}")
        for name, value in (
            ("feature_snapshot_hash", self.feature_snapshot_hash),
            ("provenance_hash", self.provenance_hash),
            ("corpus_manifest_hash", self.corpus_manifest_hash),
            ("registry_snapshot_hash", self.registry_snapshot_hash),
        ):
            _require_hash(name, value)
        for name, value in (
            ("allowed_lookback", self.allowed_lookback),
            ("forbidden_future_window", self.forbidden_future_window),
            ("label_offset", self.label_offset),
        ):
            _require_non_negative_delta(name, value)
        object.__setattr__(self, "information_set_hash", canonical_hash(self.canonical_payload()))

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "version": HF10_VERSION,
            "timing_seat": self.timing_seat,
            "observation_cutoff": _format_dt(self.observation_cutoff),
            "allowed_lookback_seconds": float(self.allowed_lookback.total_seconds()),
            "forbidden_future_window_seconds": float(self.forbidden_future_window.total_seconds()),
            "label_offset_seconds": float(self.label_offset.total_seconds()),
            "feature_snapshot_hash": self.feature_snapshot_hash,
            "provenance_hash": self.provenance_hash,
            "corpus_manifest_hash": self.corpus_manifest_hash,
            "registry_snapshot_hash": self.registry_snapshot_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_payload() | {"information_set_hash": self.information_set_hash}

    def validate(self) -> None:
        """The dataclass initializer already enforces the contract; this is a semantic alias."""
        return None


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    predictor: str
    path_seat: str | None
    timing_seat: str | None
    information_set_hash: str
    corpus_manifest_hash: str
    registry_snapshot_hash: str
    falsification_level: int
    status: str
    rationale: str
    contradictions: tuple[str, ...] = ()
    conventional_stack_hash: str | None = None

    def __post_init__(self) -> None:
        if not self.claim_id:
            raise ValueError("claim_id is required")
        if not self.predictor:
            raise ValueError("predictor is required")
        for name, value in (
            ("information_set_hash", self.information_set_hash),
            ("corpus_manifest_hash", self.corpus_manifest_hash),
            ("registry_snapshot_hash", self.registry_snapshot_hash),
        ):
            _require_hash(name, value)
        if self.status not in CLAIM_STATUSES:
            raise ValueError(f"status must be one of {CLAIM_STATUSES}")
        if self.falsification_level < 0 or self.falsification_level > 8:
            raise ValueError("falsification_level must be between 0 and 8")
        if not self.rationale:
            raise ValueError("rationale is required")
        if len(set(self.contradictions)) != len(self.contradictions):
            raise ValueError("contradictions must be unique")
        if self.conventional_stack_hash is not None:
            _require_hash("conventional_stack_hash", self.conventional_stack_hash)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "predictor": self.predictor,
            "path_seat": self.path_seat,
            "timing_seat": self.timing_seat,
            "information_set_hash": self.information_set_hash,
            "corpus_manifest_hash": self.corpus_manifest_hash,
            "registry_snapshot_hash": self.registry_snapshot_hash,
            "falsification_level": self.falsification_level,
            "status": self.status,
            "rationale": self.rationale,
            "contradictions": list(self.contradictions),
            "conventional_stack_hash": self.conventional_stack_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_payload()


@dataclass(frozen=True, slots=True)
class ClaimRegistry:
    registry_snapshot_hash: str
    claims: tuple[Claim, ...]
    status: str
    rationale: str
    conventional_stack_hash: str | None = None
    registry_version: str = HF10_VERSION

    def __post_init__(self) -> None:
        _require_hash("registry_snapshot_hash", self.registry_snapshot_hash)
        if self.status not in CLAIM_STATUSES:
            raise ValueError(f"status must be one of {CLAIM_STATUSES}")
        if not self.rationale:
            raise ValueError("rationale is required")
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(set(claim_ids)) != len(claim_ids):
            raise ValueError("claim_ids must be unique")
        for claim in self.claims:
            if claim.registry_snapshot_hash != self.registry_snapshot_hash:
                raise ValueError("claim registry_snapshot_hash must match registry_snapshot_hash")
        if self.conventional_stack_hash is not None:
            _require_hash("conventional_stack_hash", self.conventional_stack_hash)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "version": self.registry_version,
            "registry_snapshot_hash": self.registry_snapshot_hash,
            "status": self.status,
            "rationale": self.rationale,
            "conventional_stack_hash": self.conventional_stack_hash,
            "claims": [claim.to_dict() for claim in self.claims],
        }

    @property
    def claim_registry_hash(self) -> str:
        return canonical_hash(self.canonical_payload())

    def to_dict(self) -> dict[str, Any]:
        return self.canonical_payload() | {"claim_registry_hash": self.claim_registry_hash}
