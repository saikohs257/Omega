from __future__ import annotations

from typing import Any, Mapping

from bentaxis.identity import Identity
from runtime.selection import SelectionThresholds


def experiment_identity_payload(
    *,
    hypothesis_id: str,
    information_set_id: str,
    metric_contract: str,
    output_kind: str,
    output_name: str,
    output_version: str,
    implementation_id: str,
    selection_thresholds: SelectionThresholds,
) -> Mapping[str, Any]:
    return {
        "hypothesis_id": hypothesis_id,
        "information_set_id": information_set_id,
        "metric_contract": metric_contract,
        "output_kind": output_kind,
        "output_name": output_name,
        "output_version": output_version,
        "implementation_id": implementation_id,
        "selection_thresholds": selection_thresholds.canonical_payload(),
        "selection_thresholds_hash": selection_thresholds.selection_thresholds_hash,
    }


def experiment_identity(payload: Mapping[str, Any]) -> str:
    return Identity.calculate(payload).digest
