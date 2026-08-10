import pytest

from runtime.test_spine import TestSpine, TestSpineViolation


def test_locked_spine_rejects_adaptive_components() -> None:
    spine = TestSpine("holdout-1")
    with pytest.raises(TestSpineViolation):
        spine.read("pond")
    with pytest.raises(TestSpineViolation):
        spine.read("end")


def test_locked_spine_allows_non_adaptive_reader() -> None:
    assert TestSpine("holdout-1").read("court") is None


def test_unlocked_spine_is_not_a_mutation_permission() -> None:
    assert TestSpine("sandbox-1", locked=False).read("pond") is None
