from bentaxis.identity import Identity, to_canonical_bytes


def test_canonical_bytes_dict_order_is_stable() -> None:
    left = {"alpha": 1, "beta": [2, 3], "gamma": {"delta": True}}
    right = {"gamma": {"delta": True}, "beta": [2, 3], "alpha": 1}
    assert to_canonical_bytes(left) == to_canonical_bytes(right)
    assert Identity.calculate(left) == Identity.calculate(right)


def test_canonical_bytes_set_order_is_stable() -> None:
    left = frozenset([10, "test_string", False, (99, 100)])
    right = frozenset([(99, 100), False, "test_string", 10])
    assert to_canonical_bytes(left) == to_canonical_bytes(right)
    assert Identity.calculate(left) == Identity.calculate(right)


def test_identity_is_immutable() -> None:
    ident = Identity.calculate({"x": 1})
    try:
        ident.new_field = "illegal"  # type: ignore[attr-defined]
        raise AssertionError("Identity allowed mutation")
    except AttributeError:
        pass
