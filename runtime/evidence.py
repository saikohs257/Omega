from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import Identity


@dataclass(frozen=True, slots=True)
class CorpusIdentity:
    """Immutable identity for the exact evidence corpus used by an experiment."""

    corpus_name: str
    corpus_hash: str
    schema_version: str = "corpus-v1"
    source_ids: tuple[str, ...] = ()
    preprocessing_id: str = ""
    corpus_id: str = ""

    def __post_init__(self) -> None:
        payload: Mapping[str, Any] = {
            "corpus_name": self.corpus_name,
            "corpus_hash": self.corpus_hash,
            "schema_version": self.schema_version,
            "source_ids": tuple(sorted(self.source_ids)),
            "preprocessing_id": self.preprocessing_id,
        }
        object.__setattr__(self, "corpus_id", Identity.calculate(payload).digest)


@dataclass(frozen=True, slots=True)
class MetricContract:
    """Immutable semantics for a metric used to adjudicate an experiment."""

    name: str
    version: str = "v1"
    direction: str = "higher_is_better"
    parameters: tuple[tuple[str, Any], ...] = ()
    metric_contract_id: str = ""

    def __post_init__(self) -> None:
        if self.direction not in {"higher_is_better", "lower_is_better"}:
            raise ValueError("direction must be higher_is_better or lower_is_better")
        payload: Mapping[str, Any] = {
            "name": self.name,
            "version": self.version,
            "direction": self.direction,
            "parameters": tuple(sorted(self.parameters)),
        }
        object.__setattr__(self, "metric_contract_id", Identity.calculate(payload).digest)
