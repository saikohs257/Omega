from __future__ import annotations

from tools.dvqt_tournament import tournament
from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow


def _features(seed: int, i: int) -> tuple[float, float, float, float]:
    d = ((i * 17 + seed * 7) % 100) / 100.0
    v = ((i * 29 + seed * 11) % 100) / 100.0
    b = ((i * 43 + seed * 13) % 100) / 100.0
    tau = float((i * 19 + seed) % 12)
    return d, v, b, tau


def _target(d: float, v: float, b: float) -> TiamatMode:
    score = 0.45 * d + 0.35 * v + 0.20 * b
    return TiamatMode.EXCITATION if score >= 0.50 else TiamatMode.PRECURSOR


def _rows(seed: int, n: int = 96) -> list[TelemetryRow]:
    rows: list[TelemetryRow] = []
    previous_mode = TiamatMode.PRECURSOR
    for i in range(n):
        d, v, b, tau = _features(seed, i)
        rows.append(TelemetryRow(D=d, V=v, B=b, tau_mode=tau, mode=previous_mode, model_id="M3"))
        previous_mode = _target(d, v, b)
    return rows


def build_worlds() -> dict[str, list[TelemetryRow]]:
    return {f"world_{seed:02d}": _rows(seed) for seed in range(1, 21)}


def main() -> None:
    result = tournament(build_worlds())
    print("DVQT canonical tournament")
    print("scoreboard:", " -> ".join(result["scoreboard_order"]))
    for row in result["ranking"]:
        print(row)


if __name__ == "__main__":
    main()
