from __future__ import annotations

from dataclasses import dataclass

from .replay import ReplayRecord, verify_replay_chain


@dataclass(frozen=True, slots=True)
class ReplayLedger:
    records: tuple[ReplayRecord, ...] = ()

    @property
    def head(self) -> str:
        return self.records[-1].transition_hash if self.records else ""

    def append(self, record: ReplayRecord) -> "ReplayLedger":
        expected_sequence = len(self.records)
        expected_previous = self.head
        if record.sequence != expected_sequence:
            raise ValueError("replay sequence violation")
        if record.previous_hash != expected_previous:
            raise ValueError("replay predecessor violation")
        candidate = self.records + (record,)
        if not verify_replay_chain(candidate):
            raise ValueError("replay integrity violation")
        return ReplayLedger(candidate)

    def verify(self) -> bool:
        return verify_replay_chain(self.records)

    def checkpoint(self) -> tuple[str, int]:
        return self.head, len(self.records)
