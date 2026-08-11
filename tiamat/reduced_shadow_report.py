"""Harness-only report for the minimal-state shadow.

This uses a tiny deterministic contract spine solely to validate wiring. It is
NOT the blind second-spine scientific evaluation and must never be presented as
experimental evidence.
"""
from __future__ import annotations

from .disagreement_ledger import blind_replay


HARNESS_SPINE = (
    {"timestamp": "HARNESS:0", "episode_id": "harness", "B": 0.0, "V": 0.0, "D": 0.0, "mode": "Q"},
    {"timestamp": "HARNESS:1", "episode_id": "harness", "B": 0.8, "V": 0.2, "D": 0.1, "mode": "P"},
    {"timestamp": "HARNESS:2", "episode_id": "harness", "B": 0.9, "V": 0.2, "D": 0.2, "mode": "E"},
)


def main() -> None:
    report = blind_replay(HARNESS_SPINE)
    print("TIAMAT MINIMAL-STATE SHADOW HARNESS")
    print("STATUS=HARNESS_ONLY")
    print(f"rows={report.rows}")
    print(f"disagreements={report.disagreements}")
    print("SCIENTIFIC_SECOND_SPINE=NOT_RUN")


if __name__ == "__main__":
    main()
