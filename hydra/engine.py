from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .modules import (
    BurdenModule,
    HazardModule,
    LaneCoordinator,
    PersistenceModule,
    RecoveryModule,
    TrajectoryModule,
)
from .state import HydraDecision, HydraEvidence, HydraState


@dataclass(slots=True)
class HydraEngine:
    """Streamlined HYDRA coordinator.

    The coordinator is intentionally thin. Modules estimate state independently;
    the coordinator records their votes and disagreement rather than hiding it.
    TIAMAT remains a separate reference implementation.
    """

    hazard: HazardModule = field(default_factory=HazardModule)
    burden: BurdenModule = field(default_factory=BurdenModule)
    recovery: RecoveryModule = field(default_factory=RecoveryModule)
    trajectory: TrajectoryModule = field(default_factory=TrajectoryModule)
    persistence: PersistenceModule = field(default_factory=PersistenceModule)
    lanes: LaneCoordinator = field(default_factory=LaneCoordinator)

    def step(self, state: HydraState, evidence: HydraEvidence) -> HydraDecision:
        hazard = self.hazard.update(evidence, state)
        burden = self.burden.update(evidence, state)
        recovery = self.recovery.update(evidence, state)
        trajectory = self.trajectory.update(evidence, state)
        persistence = self.persistence.update(evidence, state)

        path = self.lanes.route(evidence.prev_live_deficit)
        lane_score = self.lanes.score(path, hazard, burden, recovery, trajectory)

        # Activation is deliberately conservative and transparent. It is a
        # coordinator policy, not a claim about canonical TIAMAT admission logic.
        active = (hazard >= 0.90 and burden >= 0.70) or lane_score >= 0.80
        age = evidence.episode_age_h if active else 0

        votes = {
            "hazard": "high" if hazard >= 0.80 else "low",
            "burden": "high" if burden >= 0.70 else "low",
            "recovery": "weak" if recovery < 0.35 else "healthy",
            "trajectory": "rising" if trajectory >= 0.65 else "flat_or_falling",
            "persistence": "persistent" if persistence >= 0.50 else "early",
            "lane": path,
        }
        scores = {
            "hazard": hazard,
            "burden": burden,
            "recovery": recovery,
            "trajectory": trajectory,
            "persistence": persistence,
            "lane": lane_score,
        }

        high = [hazard, burden, 1.0 - recovery, trajectory]
        mean = sum(high) / len(high)
        tension = sum(abs(x - mean) for x in high) / len(high)
        confidence = max(0.0, min(1.0, 1.0 - tension))

        if not active:
            action = "NORMAL"
            reason = "No module combination crossed the conservative activation policy."
        elif recovery < 0.35 and burden >= 0.70:
            action = "RECOVERY_FAILURE"
            reason = "High unresolved burden with weak recovery."
        elif trajectory >= 0.65 and hazard >= 0.80:
            action = "TRANSITION_RISK"
            reason = "Hazard and trajectory both indicate rising transition pressure."
        elif persistence >= 0.50:
            action = "PERSISTENT_STRESS"
            reason = "Active condition has persisted beyond the early-state window."
        else:
            action = "STRESSED"
            reason = "Active condition detected without a stronger transition signature."

        next_state = state.with_updates(
            hazard=hazard,
            burden=burden,
            recovery=recovery,
            trajectory=trajectory,
            persistence=age,
            entry_path=path,
            lane_scores={path: lane_score},
            lane_states={path: action},
            active=active,
            tension=tension,
            confidence=confidence,
        )
        disagreements = {
            "hazard_vs_burden": abs(hazard - burden),
            "burden_vs_recovery_failure": abs(burden - (1.0 - recovery)),
            "hazard_vs_trajectory": abs(hazard - trajectory),
        }
        return HydraDecision(next_state, action, reason, votes, scores, disagreements)

    def replay(self, evidence: Iterable[HydraEvidence]) -> list[HydraDecision]:
        state = HydraState()
        decisions: list[HydraDecision] = []
        for row in evidence:
            decision = self.step(state, row)
            decisions.append(decision)
            state = decision.state
        return decisions
