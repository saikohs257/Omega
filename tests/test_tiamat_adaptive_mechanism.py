from __future__ import annotations

from tiamat.adaptive_mechanism import discover
from tiamat.expanded_worlds import build_expanded_worlds


def test_adaptive_selector_uses_history_not_held_out_labels() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "reversal_after_acceleration")
    decision = discover(
        world.mechanisms,
        world.labels,
        world.predictions,
        feedback_n=20,
        budget=3,
        margin=0.02,
    )
    assert decision.abstained is False
    assert decision.probes
    assert "phase" in decision.selected
    assert all(probe.probe_index <= 3 for probe in decision.probes)


def test_adaptive_selector_abstains_on_unknown_world() -> None:
    world = next(w for w in build_expanded_worlds() if w.name == "unknown_world")
    decision = discover(
        world.mechanisms,
        world.labels,
        world.predictions,
        feedback_n=20,
        budget=3,
    )
    assert decision.abstained is True
    assert decision.selected == ()
    assert decision.probes == ()
