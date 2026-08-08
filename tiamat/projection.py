from __future__ import annotations

from typing import Any

from .state import TiamatState


def project(state: TiamatState) -> dict[str, Any]:
    """Return the canonical observable projection of TIAMAT state."""
    return state.to_dict()
