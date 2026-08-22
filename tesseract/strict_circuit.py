from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from tesseract.circuit_v1_1 import (
    effective_ohms,
    empirical_conductance,
    lit_path_score,
    release_permission_for,
    train_residual,
)
from tesseract.q4_contract import HOLD_SELF, edge as q4_edge, legal_edge


@dataclass(frozen=True, slots=True)
class StrictCircuitRow:
    edge_id: str
    from_node: str
    to_node: str
    changed_axis: int
    amp_current_residual: float
    residual_voltage_to_edge: float
    conductance: float
    ohms: float
    release_permission: float
    continuity_prior: float
    capacitance_lock: float
    lit_path_score: float
    authority_state: str = "RESEARCH_CANDIDATE"
    runtime_allowed: bool = False

    @property
    def canonical_payload(self) -> dict[str, object]:
        return {
            "schema": "tesseract-circuit-v1.1-strict-row",
            "edge_id": self.edge_id,
            "from_node": self.from_node,
            "to_node": self.to_node,
            "changed_axis": self.changed_axis,
            "amp_current_residual": self.amp_current_residual,
            "residual_voltage_to_edge": self.residual_voltage_to_edge,
            "conductance": self.conductance,
            "ohms": self.ohms,
            "release_permission": self.release_permission,
            "continuity_prior": self.continuity_prior,
            "capacitance_lock": self.capacitance_lock,
            "lit_path_score": self.lit_path_score,
            "authority_state": self.authority_state,
            "runtime_allowed": self.runtime_allowed,
        }


def build_strict_row(
    from_node: str,
    to_node: str,
    *,
    amp_current_residual: float,
    residual_voltage_to_edge: float,
    edge_release_count: float,
    risk_set_count: float,
    release_state: str,
    continuity_prior: float,
    capacitance_lock: float,
    authority_state: str = "RESEARCH_CANDIDATE",
    runtime_allowed: bool = False,
) -> StrictCircuitRow:
    edge_ref = q4_edge(from_node, to_node)
    conductance = empirical_conductance(edge_release_count, risk_set_count)
    ohms = effective_ohms(conductance)
    release_permission = release_permission_for(release_state)
    score = lit_path_score(
        amp_current_residual,
        residual_voltage_to_edge,
        conductance,
        release_permission,
        continuity_prior,
        capacitance_lock,
    )
    return StrictCircuitRow(
        edge_id=edge_ref.edge_id,
        from_node=from_node,
        to_node=to_node,
        changed_axis=edge_ref.changed_axis,
        amp_current_residual=float(amp_current_residual),
        residual_voltage_to_edge=float(residual_voltage_to_edge),
        conductance=float(conductance),
        ohms=float(ohms),
        release_permission=float(release_permission),
        continuity_prior=float(continuity_prior),
        capacitance_lock=float(capacitance_lock),
        lit_path_score=float(score),
        authority_state=str(authority_state),
        runtime_allowed=bool(runtime_allowed),
    )


def reject_nonlegal_edge(from_node: str, to_node: str) -> None:
    if not legal_edge(from_node, to_node):
        raise ValueError(f"illegal Q4 edge: {from_node!r}->{to_node!r}")


def reject_hold_self_as_edge(to_node: str) -> None:
    if to_node == HOLD_SELF:
        raise ValueError("HOLD_SELF is a control state, not a circuit edge")


def assert_reference_authority(row: StrictCircuitRow) -> None:
    if row.runtime_allowed:
        raise ValueError("strict V1.1 reference rows cannot grant runtime authority")


def residualize_train_apply(
    train_rows: Sequence[Mapping[str, object]],
    apply_rows: Sequence[Mapping[str, object]],
    *,
    value_key: str,
    group_keys: Sequence[str],
) -> tuple[list[float], list[float]]:
    return train_residual(
        train_rows,
        apply_rows,
        value_key=value_key,
        group_keys=group_keys,
    )
