"""DVQT projection tournament over the canonical 20-world discovery suite.

This intentionally reuses the established world vocabulary rather than creating
new DVQT-specific worlds. It is a bridge test for the projection tournament;
the final scientific result still requires real DVQT telemetry for each world.
"""
from __future__ import annotations

from tests.test_tiamat_tournament_20_worlds import WORLDS


def test_canonical_world_suite_is_available_for_dvqt_bridge() -> None:
    assert len(WORLDS) == 20
    assert WORLDS[-1].combo == ("charge", "coupling")
