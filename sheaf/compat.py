from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class LocalSection:
    domain: str
    values: tuple[tuple[str, Any], ...]

    @classmethod
    def create(cls, domain: str, values: dict[str, Any]) -> LocalSection:
        return cls(domain=domain, values=tuple(sorted(values.items())))

    def as_dict(self) -> dict[str, Any]:
        return dict(self.values)


@dataclass(slots=True)
class Sheaf:
    sections: list[LocalSection] = field(default_factory=list)

    def add(self, section: LocalSection) -> None:
        self.sections.append(section)

    def compatibility(self) -> bool:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for section in self.sections:
            grouped.setdefault(section.domain, []).append(section.as_dict())
        for domain, items in grouped.items():
            if not self._domain_compatible(items):
                return False
        return True

    def global_section(self) -> dict[str, dict[str, Any]] | None:
        if not self.compatibility():
            return None
        result: dict[str, dict[str, Any]] = {}
        for section in self.sections:
            domain_map = result.setdefault(section.domain, {})
            domain_map.update(section.as_dict())
        return result

    def _domain_compatible(self, items: Iterable[dict[str, Any]]) -> bool:
        items = list(items)
        if not items:
            return True
        base = items[0]
        for item in items[1:]:
            for key in set(base).intersection(item):
                if base[key] != item[key]:
                    return False
        return True
