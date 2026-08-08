"""Omega Epistemic Runtime Kernel (ERK) reference primitives."""

from .core import (
    Action,
    Authority,
    EpistemicState,
    EvidenceRecord,
    GraphEdge,
    GraphMetrics,
    GraphNode,
    PolicyConfig,
    Supervisor,
    Transition,
    compute_strain,
    graph_metrics,
    state_hash,
)
from .kernel import ConstitutionalKernel, ConstitutionalViolation, KernelConfig
from .runtime import ConstitutionalRuntime, RuntimeStep

# Load the isolated compatibility boundary after all core/kernel classes exist.
from . import compat as _compat  # noqa: F401,E402

__all__ = [
    "Action",
    "Authority",
    "ConstitutionalKernel",
    "ConstitutionalRuntime",
    "ConstitutionalViolation",
    "EpistemicState",
    "EvidenceRecord",
    "GraphEdge",
    "GraphMetrics",
    "GraphNode",
    "KernelConfig",
    "PolicyConfig",
    "RuntimeStep",
    "Supervisor",
    "Transition",
    "compute_strain",
    "graph_metrics",
    "state_hash",
]
