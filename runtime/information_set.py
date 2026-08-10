from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bentaxis.identity import Identity
from runtime.evidence import CorpusIdentity


@dataclass(frozen=True, slots=True)
class InformationSet:
    """Immutable description of exactly what information an experiment may see."""

    corpus_id: str
    feature_names: tuple[str, ...] = ()
    label_name: str = ""
    cutoff: str = ""
    source_ids: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    schema_version: str = "information-set-v1"
    information_set_id: str = ""

    @classmethod
    def from_corpus(
        cls,
        corpus: CorpusIdentity,
        *,
        feature_names: tuple[str, ...] = (),
        label_name: str = "",
        cutoff: str = "",
        source_ids: tuple[str, ...] = (),
        exclusions: tuple[str, ...] = (),
    ) -> InformationSet:
        return cls(
            corpus_id=corpus.corpus_id,
            feature_names=feature_names,
            label_name=label_name,
            cutoff=cutoff,
            source_ids=source_ids or corpus.source_ids,
            exclusions=exclusions,
        )

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
