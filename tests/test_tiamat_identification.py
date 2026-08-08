from tiamat.identification import DORMANCY_REFRACTORY_THRESHOLD, HAZARD_BANDS, hazard_band
from tiamat.model_registry import MODEL_REGISTRY, get_model


def test_permanent_model_ids_are_unique():
    ids = [model.model_id for model in MODEL_REGISTRY]
    assert len(ids) == len(set(ids))
    assert ids == ["M0", "M1", "M2", "M3", "M4", "M5", "M6", "M7"]


def test_v6_is_permanent_control():
    assert get_model("M7").permanent_control
    assert get_model("M7").state == ("F", "B", "R", "H", "O", "D", "Q", "phi")


def test_core_candidate_is_m3():
    assert get_model("M3").state == ("B", "V", "D")


def test_canonical_thresholds():
    assert HAZARD_BANDS == (0.343, 0.599, 0.794)
    assert DORMANCY_REFRACTORY_THRESHOLD == 0.95


def test_hazard_band_boundaries():
    assert hazard_band(0.342999) == 0
    assert hazard_band(0.343) == 1
    assert hazard_band(0.599) == 2
    assert hazard_band(0.794) == 3


def test_registry_rejects_unknown_id():
    try:
        get_model("M999")
    except KeyError:
        return
    raise AssertionError("unknown model IDs must be rejected")
