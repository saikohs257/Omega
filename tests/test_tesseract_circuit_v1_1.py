from tesseract.circuit_v1_1 import (
    assert_no_leakage_features,
    effective_ohms,
    empirical_conductance,
    lit_path_score,
    release_permission_for,
    train_residual,
)


def test_empirical_conductance_and_ohms_match_frozen_definition() -> None:
    conductance = empirical_conductance(9, 90)
    assert conductance == (9 + 1.0) / (90 + 1.0 + 9.0)
    assert effective_ohms(conductance) == 1.0 / (1e-6 + conductance)


def test_release_permission_state_machine_values_are_frozen() -> None:
    assert release_permission_for("HOLD_LOCKED") == 0.0
    assert release_permission_for("RELEASE_PENDING_1_6H") == 0.25
    assert release_permission_for("RELEASE_OPEN_NOW") == 1.0
    assert release_permission_for("POST_RELEASE_COOLDOWN") == 0.1
    assert release_permission_for("future_unknown_state") == 0.0


def test_train_residual_uses_train_only_group_median_and_global_fallback() -> None:
    train = [
        {"group": "a", "x": 10},
        {"group": "a", "x": 14},
        {"group": "b", "x": 20},
    ]
    apply = [
        {"group": "a", "x": 100},
        {"group": "new", "x": 30},
    ]
    train_res, apply_res = train_residual(train, apply, value_key="x", group_keys=("group",))
    # V1.1 source: known groups use train-only group medians; unseen groups
    # use the train-global median. The apply rows never determine expectation.
    assert train_res == [-2.0, 2.0, 0.0]
    assert apply_res == [88.0, 16.0]


def test_train_residual_ignores_apply_distribution_for_global_fallback() -> None:
    train = [
        {"group": "a", "x": 10},
        {"group": "a", "x": 14},
        {"group": "b", "x": 20},
    ]
    apply_a = [{"group": "new", "x": 30}]
    apply_b = [{"group": "new", "x": 3000}]
    _, residual_a = train_residual(train, apply_a, value_key="x", group_keys=("group",))
    _, residual_b = train_residual(train, apply_b, value_key="x", group_keys=("group",))
    assert residual_a == [16.0]
    assert residual_b == [2986.0]


def test_leakage_guard_rejects_future_labels() -> None:
    try:
        assert_no_leakage_features(("amp", "realized_edge", "voltage"))
    except ValueError as exc:
        assert "realized_edge" in str(exc)
    else:
        raise AssertionError("leakage guard accepted a target column")


def test_lit_path_score_is_reference_composition_not_learned_weighting() -> None:
    score = lit_path_score(2.0, 3.0, 0.5, 1.0, 1.0, 1.0)
    assert score == 3.0 / (1.0 + 1e-6)
