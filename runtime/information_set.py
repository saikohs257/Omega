from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import Identity


@dataclass(frozen=True, slots=True)
class InformationSet:
    """Immutable description of what information an experiment is allowed to see."""

    corpus_id: str
    feature_names: tuple[str, ...] = ()
    label_name: str = ""
    cutoff: str = ""
    source_ids: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    schema_version: str = "information-set-v1"
    information_set_id: str = ""

    def __post_init__(self) -> None:
        payload: Mapping[str, Any] = {
            "corpus_id": self.corpus_id,
            "feature_names": tuple(sorted(self.feature_names)),
            "label_name": self.label_name,
            "cutoff": self.cutoff,
            "source_ids": tuple(sorted(self.source_ids)),
            "exclusions": tuple(sorted(self.exclusions)),
            "schema_version": self.schema_version,
        }
        object.__setattr__(self, "information_set_id", Identity.calculate(payload).digest)
