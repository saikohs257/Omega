from tiamat.adversarial_worlds import _interaction_world


def test_interaction_is_computed_from_components_not_labels() -> None:
    labels, predictions = _interaction_world(20)
    a = predictions["A"]
    b = predictions["B"]
    axb = predictions["A_x_B"]
    expected = tuple(pa * (1.0 - pb) + (1.0 - pa) * pb for pa, pb in zip(a, b))
    assert axb == expected
    assert any(abs(p - y) > 0.05 for p, y in zip(axb, labels))


def test_interaction_components_are_marginally_uninformative() -> None:
    labels, predictions = _interaction_world(20)
    for name in ("A", "B"):
        # Balanced XOR makes each marginal component independent of the label.
        assert sum(predictions[name]) == 10.0
        assert sum(labels) == 10


def test_interaction_joint_is_informative() -> None:
    labels, predictions = _interaction_world(20)
    axb = predictions["A_x_B"]
    assert all((p > 0.8) == bool(y) for p, y in zip(axb, labels))
