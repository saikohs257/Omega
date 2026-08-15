from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Iterable, Mapping
import csv


@dataclass(frozen=True, slots=True)
class Bar:
    timestamp: datetime
    close: float
    volume: float | None = None


@dataclass(frozen=True, slots=True)
class OutcomeSpec:
    """Frozen evaluator rule; never supplied to the replay model."""

    horizon: int
    drawdown: float
    recovery_horizon: int = 0
    recovery_fraction: float = 0.0


@dataclass(frozen=True, slots=True)
class CausalObservation:
    index: int
    timestamp: datetime
    close: float
    return_1: float
    return_24: float
    state_delta: float


@dataclass(frozen=True, slots=True)
class OutcomeLabel:
    origin_index: int
    crash: bool
    min_forward_return: float
    recovery_within_horizon: bool


@dataclass(frozen=True, slots=True)
class ReplayRow:
    observation: CausalObservation
    outcome: OutcomeLabel


def load_bars_csv(path: str | Path) -> list[Bar]:
    """Load a minimal OHLCV-compatible CSV without adding a data provider."""
    rows: list[Bar] = []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {"timestamp", "close"}
        if not required.issubset(reader.fieldnames or set()):
            raise ValueError("CSV must contain timestamp and close columns")
        for raw in reader:
            ts = datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
            close = float(raw["close"])
            volume = float(raw["volume"]) if raw.get("volume") not in (None, "") else None
            if not isfinite(close) or close <= 0:
                raise ValueError("close must be finite and positive")
            rows.append(Bar(ts, close, volume))
    if any(rows[i].timestamp >= rows[i + 1].timestamp for i in range(len(rows) - 1)):
        raise ValueError("timestamps must be strictly increasing")
    return rows


def build_causal_observations(bars: Iterable[Bar]) -> list[CausalObservation]:
    """Compute features using only observations at or before each index."""
    data = list(bars)
    out: list[CausalObservation] = []
    for i, bar in enumerate(data):
        r1 = 0.0 if i == 0 else bar.close / data[i - 1].close - 1.0
        r24 = 0.0 if i < 24 else bar.close / data[i - 24].close - 1.0
        delta = 0.0 if i == 0 else r1
        out.append(CausalObservation(i, bar.timestamp, bar.close, r1, r24, delta))
    return out


def build_outcome_labels(bars: Iterable[Bar], spec: OutcomeSpec) -> list[OutcomeLabel]:
    """Label each origin from future bars only; labels never enter causal features."""
    data = list(bars)
    if spec.horizon <= 0:
        raise ValueError("horizon must be positive")
    if not 0.0 < spec.drawdown < 1.0:
        raise ValueError("drawdown must lie in (0, 1)")
    labels: list[OutcomeLabel] = []
    for i, bar in enumerate(data):
        future = data[i + 1 : i + 1 + spec.horizon]
        if not future:
            min_ret = 0.0
            labels.append(OutcomeLabel(i, False, min_ret, False))
            continue
        min_ret = min(x.close / bar.close - 1.0 for x in future)
        crash = min_ret <= -spec.drawdown
        recovered = False
        if crash and spec.recovery_horizon > 0 and spec.recovery_fraction > 0:
            low = min(x.close / bar.close for x in future)
            for x in data[i + 1 : i + 1 + spec.recovery_horizon]:
                if x.close / bar.close >= 1.0 - low * spec.recovery_fraction:
                    recovered = True
                    break
        labels.append(OutcomeLabel(i, crash, min_ret, recovered))
    return labels


def build_replay_rows(bars: Iterable[Bar], spec: OutcomeSpec) -> list[ReplayRow]:
    data = list(bars)
    observations = build_causal_observations(data)
    outcomes = build_outcome_labels(data, spec)
    return [ReplayRow(observations[i], outcomes[i]) for i in range(len(data))]


def assert_no_future_leakage(rows: Iterable[ReplayRow]) -> None:
    """Guardrail: outcome labels may exist in the ledger but never in observations."""
    for row in rows:
        obs = row.observation
        if hasattr(obs, "crash") or hasattr(obs, "min_forward_return"):
            raise AssertionError("future outcome leaked into causal observation")


def event_rows(rows: Iterable[ReplayRow]) -> Mapping[int, ReplayRow]:
    """Return only rows with a positive evaluator outcome."""
    return {row.observation.index: row for row in rows if row.outcome.crash}
