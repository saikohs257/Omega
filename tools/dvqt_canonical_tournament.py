from __future__ import annotations

from tools.dvqt_tournament import tournament
from tiamat.modes import TiamatMode
from tiamat.telemetry import TelemetryRow


def _rows(seed: int, n: int = 96) -> list[TelemetryRow]:
    rows: list[TelemetryRow] = []
    for i in range(n):
        d = ((i * 17 + seed * 7) % 100) / 100.0
        v = ((i * 29 + seed * 11) % 100) / 100.0
        b = ((i * 43 + seed * 13) % 100) / 100.0
        tau = float((i * 19 + seed) % 12)
        # The target is generated from D/V/B only. tau_mode and current mode
        # are deliberately non-causal, so the reduction can be tested honestly.
        score = 0.45 * d + 0.35 * v + 0.20 * b
        nxt = TiamatMode.EXCITATION if score >= 0.50 else TiamatMode.PRECURSOR
        rows.append(
            TelemetryRow(D=d, V=v, B=b, tau_mode=tau,
                         mode=TiamatMode.PRECURSOR, model_id="M3")
        )
        # Store the realized target as the next row's mode while preserving
        # the next row's independent state values.
        if i + 1 < n:
            rows[-1] = TelemetryRow(D=d, V=v, B=b, tau_mode=tau,
                                    mode=nxt, model_id="M3")
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
