from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence
import json

from .calibration import CalibrationReport
from .calibration_artifacts import write_calibration_artifacts
from .corpus_snapshot import CorpusSnapshot
from .holdout import HoldoutExperiment
from .identification_registry import MODEL_REGISTRY
from .metric_contract import ProbabilityPredictor
from .telemetry import TelemetryRow


@dataclass(frozen=True, slots=True)
class DiagnosticPredictors:
    """Predictors supplied to the calibration diagnostic.

    Controls-only execution is intentionally permitted. It validates the frozen
    corpus -> metric contract -> artifact path before any candidate selector can run.
    """
    controls: Mapping[str, ProbabilityPredictor]
    candidates: Mapping[str, ProbabilityPredictor]

    def __post_init__(self) -> None:
        overlap = set(self.controls) & set(self.candidates)
        if overlap:
            raise ValueError(f"predictor IDs cannot be both control and candidate: {sorted(overlap)}")
        if not self.controls and not self.candidates:
            raise ValueError("at least one control or candidate predictor is required")


@dataclass(frozen=True, slots=True)
class DiagnosticRun:
    report: CalibrationReport
    artifact_path: Path


def load_json_rows(path: str | Path) -> tuple[dict, ...]:
    """Load a deterministic JSON array or JSONL corpus snapshot."""
    payload = Path(path).read_text(encoding="utf-8")
    try:
        decoded = json.loads(payload)
    except json.JSONDecodeError:
        rows = [json.loads(line) for line in payload.splitlines() if line.strip()]
    else:
        rows = decoded
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("corpus must be a JSON array or JSONL object stream")
    return tuple(dict(row) for row in rows)


def run_diagnostic(
    rows: Sequence[Mapping[str, object] | TelemetryRow],
    *,
    experiment: HoldoutExperiment,
    predictors: DiagnosticPredictors,
    run_id: str,
    artifact_root: str | Path,
    inference_purity: bool = True,
    ece_reliability_behavior: str = "",
) -> DiagnosticRun:
    """Run calibration diagnostics and persist them through the canonical writer.

    This function deliberately performs no model selection. Controls and candidates
    are passed directly to HoldoutExperiment.calibration_report(), which routes
    them through CalibrationDiagnostic and MetricContract.
    """
    if not inference_purity:
        raise ValueError("real diagnostic execution requires inference_purity=True")
    if not ece_reliability_behavior.strip():
        raise ValueError("ece_reliability_behavior is required before diagnostic execution")

    source = tuple(row.to_mapping() if isinstance(row, TelemetryRow) else dict(row) for row in rows)
    snapshot = CorpusSnapshot.freeze(source)
    snapshot.verify()
    report = experiment.calibration_report(
        snapshot.rows,
        controls=predictors.controls,
        candidates=predictors.candidates,
        inference_purity=inference_purity,
        ece_reliability_behavior=ece_reliability_behavior,
    )
    snapshot.verify()
    artifact_path = write_calibration_artifacts(report, root=artifact_root, run_id=run_id)
    return DiagnosticRun(report=report, artifact_path=artifact_path)


def registry_model_ids() -> tuple[str, ...]:
    return tuple(sorted(MODEL_REGISTRY))
