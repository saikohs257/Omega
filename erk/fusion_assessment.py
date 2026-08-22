"""ERK assessment of an Oracle FusionObject.

This is deliberately observational: it produces an epistemic assessment and
never mutates TIAMAT state or grants execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from oracle.fusion import FusionObject


@dataclass(frozen=True, slots=True)
class FusionAssessment:
    confidence: float
    uncertainty: float
    disagreement: float
    missing_channel_ratio: float
    evidence_concentration: float
    novelty: float
    calibration_penalty: float
    reasons: tuple[str, ...]
    metadata: Mapping[str, Any]

    @property
    def risk_flags(self) -> tuple[str, ...]:
        flags = []
        if self.disagreement > 0.0:
            flags.append("DISAGREEMENT")
        if self.missing_channel_ratio > 0.0:
            flags.append("MISSING_EVIDENCE")
        if self.evidence_concentration >= 0.75:
            flags.append("CONCENTRATED_EVIDENCE")
        if self.novelty >= 0.75:
            flags.append("NOVEL_REGIME")
        if self.calibration_penalty > 0.0:
            flags.append("CALIBRATION_PENALTY")
        return tuple(flags)


def assess_fusion(
    fusion: FusionObject,
    *,
    novelty: float = 0.0,
    calibration_error: float = 0.0,
) -> FusionAssessment:
    """Evaluate evidence quality without interpreting domain truth."""
    if not 0.0 <= novelty <= 1.0:
        raise ValueError("novelty must be in [0, 1]")
    if not 0.0 <= calibration_error <= 1.0:
        raise ValueError("calibration_error must be in [0, 1]")

    sources = fusion.sources
    total_weight = sum(max(0.0, claim.confidence * claim.freshness) for claim in fusion.claims)
    if not sources or total_weight <= 0.0:
        concentration = 1.0 if fusion.claims else 0.0
    else:
        weights = {}
        for claim in fusion.claims:
            weights[claim.source] = weights.get(claim.source, 0.0) + max(0.0, claim.confidence * claim.freshness)
        concentration = max(weights.values()) / total_weight

    expected = len(fusion.missing_channels) + len(sources)
    missing_ratio = len(fusion.missing_channels) / expected if expected else 0.0
    calibration_penalty = calibration_error
    uncertainty = min(
        1.0,
        0.35 * fusion.disagreement
        + 0.20 * missing_ratio
        + 0.20 * concentration
        + 0.15 * novelty
        + 0.10 * calibration_penalty,
    )
    confidence = max(0.0, min(1.0, fusion.confidence * (1.0 - uncertainty)))

    reasons = []
    if fusion.disagreement > 0.0:
        reasons.append("distributed claims disagree")
    if fusion.missing_channels:
        reasons.append("expected evidence channels are missing")
    if concentration >= 0.75:
        reasons.append("evidence is concentrated in one source")
    if novelty >= 0.75:
        reasons.append("evidence context is novel")
    if calibration_error > 0.0:
        reasons.append("calibration penalty supplied")

    return FusionAssessment(
        confidence=confidence,
        uncertainty=uncertainty,
        disagreement=fusion.disagreement,
        missing_channel_ratio=missing_ratio,
        evidence_concentration=concentration,
        novelty=novelty,
        calibration_penalty=calibration_penalty,
        reasons=tuple(reasons),
        metadata={"sources": sources, "phases": fusion.phases},
    )
