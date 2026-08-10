from runtime.selection import SelectionThresholds


def test_threshold_hash_is_deterministic() -> None:
    a = SelectionThresholds()
    b = SelectionThresholds()
    assert a.selection_thresholds_hash == b.selection_thresholds_hash


def test_numeric_threshold_change_changes_hash() -> None:
    a = SelectionThresholds()
    b = SelectionThresholds(brier_skill_min=0.06)
    assert a.selection_thresholds_hash != b.selection_thresholds_hash


def test_semantic_version_change_changes_hash() -> None:
    a = SelectionThresholds()
    b = SelectionThresholds(version="selection-thresholds-v2")
    assert a.selection_thresholds_hash != b.selection_thresholds_hash


def test_canonical_field_order_does_not_change_hash() -> None:
    thresholds = SelectionThresholds()
    payload = thresholds.canonical_payload()
    reordered = {"ece_max": payload["ece_max"], "version": payload["version"], "auc_min": payload["auc_min"], "brier_skill_min": payload["brier_skill_min"]}
    assert SelectionThresholds(**{k: reordered[k] for k in ("brier_skill_min", "auc_min", "ece_max", "version")}).selection_thresholds_hash == thresholds.selection_thresholds_hash
