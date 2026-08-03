from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from runtime.workers import Worker, WorkerTrace


@dataclass(frozen=True, slots=True)
class ColonyRoundResult:
    state: dict[str, Any]
    traces: tuple[WorkerTrace, ...]


@dataclass(slots=True)
class ColonyScheduler:
    workers: list[Worker] = field(default_factory=list)

    def register(self, worker: Worker) -> None:
        self.workers.append(worker)

    def run_round(self, state: Mapping[str, Any]) -> ColonyRoundResult:
        current = dict(state)
        traces: list[WorkerTrace] = []
        for worker in self.workers:
            current, trace = worker.run(current)
            traces.append(trace)
        return ColonyRoundResult(state=current, traces=tuple(traces))

    def run_rounds(self, state: Mapping[str, Any], rounds: int) -> ColonyRoundResult:
        current = dict(state)
        all_traces: list[WorkerTrace] = []
        for _ in range(rounds):
            result = self.run_round(current)
            current = result.state
            all_traces.extend(result.traces)
        return ColonyRoundResult(state=current, traces=tuple(all_traces))
