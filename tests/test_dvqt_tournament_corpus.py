"""DVQT projection tournament over the canonical 20-world discovery suite.

The suite is loaded by file path because CI runs pytest from /tmp and the
repository's tests directory is intentionally not a Python package.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_SUITE = Path(__file__).with_name("test_tiamat_tournament_20_worlds.py")
_SPEC = importlib.util.spec_from_file_location("canonical_tiamat_worlds", _SUITE)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
WORLDS = _MODULE.WORLDS


def test_canonical_world_suite_is_available_for_dvqt_bridge() -> None:
    assert len(WORLDS) == 20
    assert WORLDS[-1].combo == ("charge", "coupling")
