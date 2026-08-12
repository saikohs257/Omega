from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from .modes import TiamatMode


PATHBOOK_VERSION = "TIAMAT_PATHBOOK_V1"
HEAD_IDS = ("H0", "H2", "H3", "H4")


class PathbookExtractionError(ValueError):
    """Raised when route/timing provenance is insufficient for a legal extraction."""


@dataclass(frozen=True, slots=True)
class PathbookRoute:
    """One episode in the native Pathbook extraction.

    start_transition_path is deliberately nullable: the extractor never invents
    the legacy doorway label when the source does not establish it.
    topology_path is also nullable unless a topology route is explicitly
    established by source metadata or the native H4 ceiling condition.
    """

    episode_id: str
    start_transition_path: str | None
    topology_path: str | None
    active_burden: float | None
    exit_bridge_deficit: float | None
    prior_carry_deficit: float | None
    episode_start_time: str
    episode_end_time: str
    next_trigger_6h: float | None = None
    next_trigger_24h: float | None = None
    next_trigger_48h: float | None = None
    head_id: str | None = None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "start_transition_path": self.start_transition_path,
            "topology_path": self.topology_path,
            "ActiveBurden": self.active_burden,
            "ExitBridgeDeficit": self.exit_bridge_deficit,
            "PriorCarryDeficit": self.prior_carry_deficit,
            "episode_start_time": self.episode_start_time,
            "episode_end_time": self.episode_end_time,
            "next_trigger_6h": self.next_trigger_6h,
            "next_trigger_24h": self.next_trigger_24h,
            "next_trigger_48h": self.next_trigger_48h,
            "head_id": self.head_id,
        }


def _timestamp(row: Mapping[str, Any]) -> datetime:
    raw = row.get("timestamp")
    if not isinstance(raw, str) or not raw:
        raise PathbookExtractionError("native route extraction requires timestamp on every row")
    value = raw.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise PathbookExtractionError(f"invalid timestamp: {raw!r}") from exc


def _mode(row: Mapping[str, Any]) -> str:
    value = row.get("mode", TiamatMode.QUIESCENT.value)
    return value.value if isinstance(value, TiamatMode) else str(value)


def _burden(row: Mapping[str, Any]) -> float | None:
    # ActiveBurden is the runtime surface-pressure seat. LiveDeficit is accepted
    # only as the explicitly documented legacy source; it is never renamed into
    # ExitBridgeDeficit or PriorCarryDeficit here.
    for key in ("ActiveBurden", "active_burden", "LiveDeficit", "cp15_LiveDeficit"):
        if key in row and row[key] is not None:
            return float(row[key])
    return None


def _episode_id(row: Mapping[str, Any], fallback: int) -> str:
    value = row.get("episode_id")
    if value is None:
        raise PathbookExtractionError(
            "native route extraction requires explicit episode_id; refusing to infer episode boundaries from field names"
        )
    return str(value)


def _path(row: Mapping[str, Any], key: str) -> str | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    value = str(value)
    if value not in {"0_to_4", "2_to_4", "3_to_4", "4_to_4"}:
        raise PathbookExtractionError(f"invalid {key}: {value!r}")
    return value


def extract_pathbook_routes(rows: Sequence[Mapping[str, Any]]) -> tuple[PathbookRoute, ...]:
    """Extract the native Pathbook route/timing table without granting authority.

    The extractor is intentionally conservative. Episode identity and boundary
    rows must be explicit. Timing seats are derived from those boundaries; path
    seats are preserved from source metadata when available and are never guessed.
    """
    if not rows:
        return ()

    normalized = tuple(dict(row) for row in rows)
    timestamps = tuple(_timestamp(row) for row in normalized)
    if tuple(sorted(timestamps)) != timestamps:
        raise PathbookExtractionError("rows must be in deterministic timestamp order")

    groups: list[tuple[str, list[Mapping[str, Any]]]] = []
    current_id: str | None = None
    current: list[Mapping[str, Any]] = []
    for index, row in enumerate(normalized):
        episode_id = _episode_id(row, index)
        if current_id is None:
            current_id = episode_id
        if episode_id != current_id:
            groups.append((current_id, current))
            current_id, current = episode_id, []
        current.append(row)
    if current_id is not None:
        groups.append((current_id, current))

    output: list[PathbookRoute] = []
    prior_exit: float | None = None
    for episode_id, episode_rows in groups:
        start = episode_rows[0]
        end = episode_rows[-1]
        start_time = _timestamp(start)
        end_time = _timestamp(end)
        if end_time < start_time:
            raise PathbookExtractionError(f"episode {episode_id!r} has reversed boundaries")

        exit_bridge = _burden(end)
        active = _burden(start)

        # PriorCarryDeficit is a timing seat: previous episode's exit bridge.
        carry = prior_exit

        # A 4_to_4 topology route is legal only when the source explicitly marks
        # the ceiling head/path. No start-transition label is synthesized for it.
        topology = _path(end, "topology_path") or _path(start, "topology_path")
        head_id = end.get("head_id") or start.get("head_id")
        if head_id is not None:
            head_id = str(head_id)
            if head_id not in HEAD_IDS:
                raise PathbookExtractionError(f"invalid head_id: {head_id!r}")
            if head_id == "H4" and topology is None:
                topology = "4_to_4"

        start_transition = _path(start, "start_transition_path")
        if topology == "4_to_4" and start_transition == "4_to_4":
            raise PathbookExtractionError("4_to_4 must not be fabricated as a legacy start-transition doorway")

        output.append(
            PathbookRoute(
                episode_id=episode_id,
                start_transition_path=start_transition,
                topology_path=topology,
                active_burden=active,
                exit_bridge_deficit=exit_bridge,
                prior_carry_deficit=carry,
                episode_start_time=start_time.isoformat(),
                episode_end_time=end_time.isoformat(),
                next_trigger_6h=end.get("next_trigger_6h"),
                next_trigger_24h=end.get("next_trigger_24h"),
                next_trigger_48h=end.get("next_trigger_48h"),
                head_id=head_id,
            )
        )
        prior_exit = exit_bridge

    return tuple(output)
