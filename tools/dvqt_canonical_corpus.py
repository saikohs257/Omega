from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow


LABELS = (0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1)

# Each world gets one declared mechanism.  The generator deliberately encodes
# that mechanism into one canonical control axis while keeping the target
# transition one step ahead.  This is a synthetic falsification corpus, not a
# claim about historical TIAMAT telemetry.
AXIS_BY_WORLD: Mapping[str, str] = {
    "damage": "D",
    "recovery": "V",
    "charge": "B",
    "momentum": "tau_mode",
    "residual_momentum": "tau_mode",
    "residual_load": "D",
    "forcing": "B",
    "flow": "V",
    "initial_velocity": "V",
    "initial_momentum": "tau_mode",
    "initial_trajectory": "tau_mode",
    "path": "tau_mode",
    "trajectory": "tau_mode",
    "arc": "tau_mode",
    "route": "tau_mode",
    "track": "tau_mode",
    "orbit": "tau_mode",
    "resistance": "D",
    "coupling": "V",
}


def _signal_value(axis: str, label: int, index: int) -> float:
    # Two repeated levels make state buckets statistically estimable while
    # remaining well inside TelemetryRow's domain constraints.
    if axis in {"D", "V", "B"}:
        return 0.15 if label == 0 else 0.85
    return 2.0 if label == 0 else 8.0


def _mode(label: int) -> TiamatMode:
    return TiamatMode.EXCITATION if label else TiamatMode.PRECURSOR


def world_rows(world_name: str) -> tuple[TelemetryRow, ...]:
    axis = AXIS_BY_WORLD[world_name]
    rows: list[TelemetryRow] = []
    for i, label in enumerate(LABELS):
        values = {"D": 0.5, "V": 0.5, "B": 0.5, "tau_D": 4.0, "tau_mode": 4.0}
        values[axis] = _signal_value(axis, label, i)
        # The current mode is deliberately not used as the causal signal;
        # it records the current state while the benchmark predicts next mode.
        rows.append(
            TelemetryRow(
                D=values["D"],
                V=values["V"],
                B=values["B"],
                tau_D=values["tau_D"],
                tau_mode=values["tau_mode"],
                mode=TiamatMode.PRECURSOR,
                timestamp=f"{i:04d}",
                extras={"world": world_name, "mechanism_axis": axis, "target": label},
            )
        )
    return tuple(rows)


def canonical_worlds() -> dict[str, tuple[TelemetryRow, ...]]:
    return {name: world_rows(name) for name in AXIS_BY_WORLD}
