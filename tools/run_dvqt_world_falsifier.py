from __future__ import annotations

import json

from tiamat.adversarial_worlds import build_adversarial_worlds
from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow
from tools.dvqt_world_falsifier import analyze_worlds


def _world_rows(world):
    """Turn each deterministic world into a neutral telemetry spine.

    This is a laboratory diagnostic only: predictions become V, while B/D/mode
    and timers are fixed. It deliberately cannot claim to reconstruct hidden
    physics; it exists to exercise the collision machinery end-to-end.
    """
    rows = []
    for i, value in enumerate(world.predictions[next(iter(world.predictions))]):
        rows.append(
            TelemetryRow(
                B=0.0,
                D=0.5,
                V=float(value),
                mode=TiamatMode.PRECURSOR,
                tau_mode=float(i),
                timestamp=str(i),
            )
        )
    return tuple(rows)


def main() -> None:
    worlds = {world.name: _world_rows(world) for world in build_adversarial_worlds()}
    print(json.dumps(analyze_worlds(worlds), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
