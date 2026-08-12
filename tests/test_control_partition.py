from runtime.control_partition import preflight_controls


def test_controls_partition_is_non_fatal() -> None:
    partition = preflight_controls({
        "good": (0.1, 0.9),
        "bad": (0.1, 1.2),
    })

    assert partition.valid == ("good",)
    assert partition.incomparable_count == 1
    assert partition.reason_for("bad") is not None


def test_controls_partition_is_order_stable() -> None:
    left = preflight_controls({"b": (0.2, 0.8), "a": (0.1, 0.9)})
    right = preflight_controls({"a": (0.1, 0.9), "b": (0.2, 0.8)})
    assert left.valid == right.valid == ("a", "b")
