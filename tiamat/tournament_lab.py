"""End-to-end adversarial tournament harness for TIAMAT identification.

The harness runs the blinded synthetic worlds through the same TournamentRunner
used by ordinary cases, then compares the resulting decisions with the worlds'
held-out expectations. The generating mechanism is used only for the audit
report; it is never supplied to the selector.
"""
from __future__ import annotations

from dataclasses import dataclass

from .tournament import TournamentResult, TournamentRunner
from .world_lab import WorldExpectation, build_world_lab


@dataclass(frozen=True, slots=True)
class WorldAudit:
    expectation: WorldExpectation
    result: TournamentResult
    expectation_met: bool


@dataclass(frozen=True, slots=True)
class TournamentLabReport:
    audits: tuple[WorldAudit, ...]

    @property
    def selected(self) -> tuple[WorldAudit, ...]:
        return tuple(a for a in self.audits if a.result.decision.status == "SELECTED")

    @property
    def unresolved(self) -> tuple[WorldAudit, ...]:
        return tuple(a for a in self.audits if a.result.decision.status == "UNRESOLVED")

    @property
    def failures(self) -> tuple[WorldAudit, ...]:
        return tuple(a for a in self.audits if not a.expectation_met)

    @property
    def passed(self) -> bool:
        return not self.failures


def run_adversarial_tournament(*, max_size: int = 4) -> TournamentLabReport:
    """Run every deterministic adversarial world through the blinded tournament."""
    cases, expectations = build_world_lab(max_size=max_size)
    results = TournamentRunner().run(cases)
    audits = tuple(
        WorldAudit(
            expectation=expectation,
            result=result,
            expectation_met=_meets_expectation(expectation, result),
        )
        for expectation, result in zip(expectations, results, strict=True)
    )
    return TournamentLabReport(audits)


def _meets_expectation(expectation: WorldExpectation, result: TournamentResult) -> bool:
    selected = result.decision.selected_model_id
    truth = expectation.truth_mechanism
    if truth == "none":
        return selected is None and result.decision.status == "UNRESOLVED"
    if truth == "state_or_damage":
        return selected in {"state", "damage"}
    if truth == "calibrated":
        return selected == "calibrated"
    if truth == "A_x_B":
        return selected == "A_x_B"
    return selected == truth
