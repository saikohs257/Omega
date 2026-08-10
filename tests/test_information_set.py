from runtime.information_set import InformationSet


def test_information_set_identity_is_order_independent() -> None:
    left = InformationSet("corpus-1", ("b", "a"), "y", "2026-01-01", ("s2", "s1"))
    right = InformationSet("corpus-1", ("a", "b"), "y", "2026-01-01", ("s1", "s2"))
    assert left.information_set_id == right.information_set_id


def test_information_set_changes_when_cutoff_changes() -> None:
    left = InformationSet("corpus-1", ("a",), "y", "2026-01-01")
    right = InformationSet("corpus-1", ("a",), "y", "2026-01-02")
    assert left.information_set_id != right.information_set_id
