from dic import DIC, SidecarEvidence


def test_dic_collects_without_authority() -> None:
    dic = DIC()
    dic.emit(SidecarEvidence("chug", "RECOVERY", 0.9, 0.8))
    dic.emit(SidecarEvidence("exit_latch", "EXIT", True, 0.7))

    claims = dic.to_oracle_claims()
    assert tuple(c.source for c in claims) == ("chug", "exit_latch")
    assert not hasattr(dic, "transition")
    assert not hasattr(dic, "approved")


def test_sidecar_state_is_observable_and_bounded_by_collection_scope() -> None:
    dic = DIC()
    dic.emit(
        SidecarEvidence(
            "hinge",
            "PRESSURE",
            0.6,
            0.9,
            state_observation={"window": 60},
        )
    )
    evidence = dic.claims()[0]
    assert evidence.state_observation["window"] == 60
    assert evidence.provenance == {}
