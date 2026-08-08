"""Historical ERK compatibility shim retained for forensic reference only.

This module is intentionally not imported by the package runtime. Its behavior
was used during the ERK contract recovery phase and must not become an implicit
runtime dependency again.
"""
from __future__ import annotations

import math
from . import core as _core
from . import kernel as _kernel


def _supervise(self: _core.Supervisor, state: _core.EpistemicState) -> _core.Action:
    state = state.normalized()
    if state.cycles:
        return _core.Action.REJECT
    if state.strain >= self.config.u_crit:
        return _core.Action.QUARANTINE
    if state.calibration_error >= self.config.calibration_crit:
        return _core.Action.ESCALATE
    if state.unsupported_depth >= self.config.depth_bound:
        return _core.Action.ESCALATE
    if state.active_branches >= self.config.branch_bound:
        return _core.Action.BLOCK
    if state.authority == _core.Authority.EXECUTE:
        return _core.Action.ENABLE_EXECUTION
    return _core.Action.BLOCK


if not hasattr(_core.Supervisor, "supervise"):
    _core.Supervisor.supervise = _supervise

_original_strain = _core.compute_strain


def _compute_strain(*args, **kwargs):
    lam = kwargs.get("lam", args[4] if len(args) > 4 else 1.0)
    try:
        return _original_strain(*args, **kwargs)
    except ValueError as exc:
        try:
            invalid = not math.isfinite(float(lam)) or float(lam) < 0
        except (TypeError, ValueError, OverflowError):
            invalid = True
        if invalid:
            raise ValueError("lam must be finite and non-negative") from exc
        raise


_core.compute_strain = _compute_strain
_original_transition_apply = _core.Transition.apply


@staticmethod
def _transition_apply(state, action, evidence=(), authorized_authority=None, branch_bound=16):
    evidence = tuple(evidence)
    if authorized_authority is not None and not evidence and action is not _core.Action.ESCALATE:
        raise ValueError("authority escalation requires kernel authorization")
    return _original_transition_apply(state, action, evidence, authorized_authority=authorized_authority, branch_bound=branch_bound)


_core.Transition.apply = _transition_apply
_original_kernel_step = _kernel.ConstitutionalKernel.step


def _kernel_step(self, state, action, evidence=()):
    evidence = tuple(evidence)
    after = _original_kernel_step(self, state, action, evidence)
    grants = [r.authority_grant for r in evidence if r.authority_grant is not None]
    if grants and action is not _core.Action.ESCALATE:
        numeric = int(float(grants[0]))
        after = _core.replace(after, authority=_core.Authority(numeric)).normalized()
    return after


_kernel.ConstitutionalKernel.step = _kernel_step
