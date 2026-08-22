"""Non-authoritative ERK -> TIAMAT assessment bridge.

The bridge carries epistemic assessment as evidence. It deliberately has no
method that mutates TIAMAT state or grants execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from erk.fusion_assessment import FusionAssessment


@dataclass(frozen=True, slots=True)
class TiamatAssessment:
    confidence: float
    uncertainty: float
    flags: tuple[str, ...]
    evidence: Mapping[str, Any]


def to_tiamat_assessment(assessment: FusionAssessment) -> TiamatAssessment:
    return TiamatAssessment(
        confidence=assessment.confidence,
        uncertainty=assessment.uncertainty,
        flags=assessment.risk_flags,
        evidence={
            "disagreement": assessment.disagreement,
            "missing_channel_ratio": assessment.missing_channel_ratio,
            "evidence_concentration": assessment.evidence_concentration,
            "novelty": assessment.novelty,
            "calibration_penalty": assessment.calibration_penalty,
            "reasons": assessment.reasons,
        },
    )
