from pytest import approx

from tiamat.adversarial_worlds import _interaction_world
from tiamat.model_selection import CandidateSpec, evaluate_candidate


def test_interaction_is_computed_from_components_not_labels() -> None:
    labels, predictions = _interaction_world(20)
    a = predictions["A"]
    b = predictions["B"]
    axb = predictions["A_x_B"]
    expected = tuple(pa * (1.0 - pb) + (1.0 - pa) * pb for pa, pb in zip(a, b))
    assert axb == expected
    assert any(abs(p - y) > 0.05 for p, y in zip(axb, labels))


def test_interaction_joint_does_not_change_when_labels_are_permuted() -> None:
    labels, predictions = _interaction_world(20)
    a = predictions["A"]
    b = predictions["B"]
    axb = predictions["A_x_B"]
    permuted = labels[1:] + labels[:1]
    expected = tuple(pa * (1.0 - pb) + (1.0 - pa) * pb for pa, pb in zip(a, b))
    assert permuted != labels
    assert axb == expected
    assert axb == expected


def test_interaction_components_have_no_discriminative_advantage() -> None:
    labels, predictions = _interaction_world(20)
    for name in ("A", "B"):
        metric = evaluate_candidate(CandidateSpec(name, (name,)), predictions[name], labels)
        assert metric.auc == approx(0.5)
        assert metric.brier > 0.20


def test_interaction_components_are_marginally_uninformative() -> None:
    labels, predictions = _interaction_world(20)
    for name in ("A", "B"):
        assert sum(predictions[name]) == 10.0
        assert sum(labels) == 10


def test_interaction_joint_is_informative() -> None:
    labels, predictions = _interaction_world(20)
    axb = predictions["A_x_B"]
    metric = evaluate_candidate(CandidateSpec("A_x_B", ("A", "B")), axb, labels)
    assert all((p > 0.8) == bool(y) for p, y in zip(axb, labels))
    assert metric.auc == approx(1.0)
    assert metric.brier < 0.05
    assert metric.brier_skill > 0.80
