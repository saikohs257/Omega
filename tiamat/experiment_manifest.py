from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

MANIFEST_VERSION = "experiment-manifest-v2"


def _canonical(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda p: str(p[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(v) for v in value), key=repr)
    return value


def canonical_hash(value: Any) -> str:
    payload = json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    """Identity DAG for a reproducible TIAMAT experiment."""

    config_hash: str
    corpus_hash: str
    feature_provenance_hash: str
    label_provenance_hash: str
    model_registry_hash: str
    probability_contract_hash: str
    implementation_hash: str
    manifest_version: str = MANIFEST_VERSION

    def __post_init__(self) -> None:
        fields = (
            self.config_hash, self.corpus_hash, self.feature_provenance_hash,
            self.label_provenance_hash, self.model_registry_hash,
            self.probability_contract_hash, self.implementation_hash,
        )
        if any(not str(value) for value in fields):
            raise ValueError("all experiment manifest identity components are required")

    def dependency_payload(self) -> dict[str, object]:
        return {
            "corpus_hash": self.corpus_hash,
            "feature_provenance_hash": self.feature_provenance_hash,
            "label_provenance_hash": self.label_provenance_hash,
            "model_registry_hash": self.model_registry_hash,
            "probability_contract_hash": self.probability_contract_hash,
            "config_hash": self.config_hash,
            "implementation_hash": self.implementation_hash,
        }

    def canonical_payload(self) -> dict[str, object]:
        return {"manifest_version": self.manifest_version, **self.dependency_payload()}

    @property
    def experiment_id(self) -> str:
        return canonical_hash(self.canonical_payload())

    def to_dict(self) -> dict[str, object]:
        return self.canonical_payload() | {"experiment_id": self.experiment_id}


def corpus_fingerprint(rows: Sequence[Mapping[str, Any]]) -> str:
    return canonical_hash(list(rows))


def provenance_fingerprint(payload: Any) -> str:
    return canonical_hash(payload)


def model_registry_fingerprint(registry: Mapping[str, Any]) -> str:
    payload = {}
    for model_id, spec in sorted(registry.items(), key=lambda p: str(p[0])):
        if hasattr(spec, "__dataclass_fields__"):
            from dataclasses import asdict
            payload[str(model_id)] = asdict(spec)
        elif hasattr(spec, "__dict__"):
            payload[str(model_id)] = dict(spec.__dict__)
        else:
            payload[str(model_id)] = spec
    return canonical_hash(payload)


def implementation_fingerprint(*, commit_sha: str, schema_versions: Sequence[str] = ()) -> str:
    if not commit_sha:
        raise ValueError("commit_sha is required for implementation identity")
    return canonical_hash({"commit_sha": commit_sha, "schema_versions": sorted(str(v) for v in schema_versions)})
