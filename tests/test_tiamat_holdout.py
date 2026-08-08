from __future__ import annotations

from tiamat import HoldoutExperiment, IdentificationRunner

ROWS = [
    {"timestamp": "2026-08-08T10:03:00Z", "B": 0.2, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 0.0, "mode": "Q"},
    {"timestamp": "2026-08-08T10:01:00Z", "B": 0.0, "V": 0.0, "D": 0.0, "tau_D": 0.0, "tau_mode": 1.0, "mode": "Q"},
    {"timestamp": "2026-08-08T10:06:00Z", "B": 0.4, "V": -0.1, "D": 0.3, "tau_D": 3.0, "tau_mode": 4.0, "mode": "R"},
    {"timestamp": "2026-08-08T10:02:00Z", "B": 0.1, "V": 0.1, "D": 0.0, "tau_D": 0.0, "tau_mode": 2.0, "mode": "P"},
    {"timestamp": "2026-08-08T10:05:00Z", "B": 0.5, "V": 0.2, "D": 0.4, "tau_D": 4.0, "tau_mode": 5.0, "mode": "H"},
    {"timestamp": "2026-08-08T10:04:00Z", "B": 0.3, "V": 0.0, "D": 0.2, "tau_D": 2.0, "tau_mode": 3.0, "mode": "C"},
]

def test_holdout_split_orders_temporally_and_uses_all_rows() -> None:
    split = HoldoutExperiment().split_rows(ROWS)
    assert split.sizes == {"train": 4, "validation": 1, "test": 1}
    assert [row.timestamp for row in split.train] == ["2026-08-08T10:01:00Z", "2026-08-08T10:02:00Z", "2026-08-08T10:03:00Z", "2026-08-08T10:04:00Z"]
    assert [row.timestamp for row in split.validation] == ["2026-08-08T10:05:00Z"]
    assert [row.timestamp for row in split.test] == ["2026-08-08T10:06:00Z"]

def test_holdout_evaluation_reports_three_splits_and_validation_selection() -> None:
    evaluation = IdentificationRunner().evaluate_holdout(ROWS, model_ids=("M0", "M3", "M7"))
    payload = evaluation.to_dict()
    assert payload["version"] == "holdout-v1"
    assert payload["split"]["sizes"] == {"train": 4, "validation": 1, "test": 1}
    assert {split["name"] for split in payload["splits"]} == {"train", "validation", "test"}
    assert evaluation.selected_model_id in {"M0", "M3", "M7"}
    assert evaluation.validation.winner is not None
