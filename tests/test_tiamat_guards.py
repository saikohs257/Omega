import math

import pytest

from tiamat import TiamatMode, TiamatState
from tiamat.guards import evaluate_guards


def _result(results, name):
    return next(result for result in results if result.name == name)


def test_malformed_numeric_guard_evidence_is_deterministically_ignored():
    state = TiamatState(D=.9, V=.2, tau_mode=4, mode=TiamatMode.RELAXATION)
    results = evaluate_guards(
        state,
        {
            "damage_threshold": "not-a-number",
            "residual_threshold": math.inf,
            "excitation_duration": math.nan,
            "precursor_threshold": object(),
            "promotion_threshold": "1.5",
            "promotion_count": "2",
        },
    )

    assert not _result(results, "DURATION_DAMAGE_HAZARD_GUARD").triggered
    assert not _result(results, "RELAXATION_WITH_RESIDUAL_DAMAGE").triggered
    assert not _result(results, "EXCITATION_DURATION_EXPIRED").triggered
    assert not _result(results, "LATENT_HAZARD_PRECURSOR_GUARD").triggered
    assert not _result(results, "COUPLED_TRANSFER_HAZARD_PROMOTION").triggered


def test_guard_evidence_must_be_mapping():
    with pytest.raises(TypeError, match="evidence must be a mapping"):
        evaluate_guards(TiamatState(), [])


def test_valid_integer_promotion_evidence_still_triggers():
    state = TiamatState(mode=TiamatMode.COUPLED_TRANSFER)
    results = evaluate_guards(
        state,
        {"promotion_threshold": 2, "promotion_count": 2},
    )
    assert _result(results, "COUPLED_TRANSFER_HAZARD_PROMOTION").triggered
