from sheaf.compat import LocalSection, Sheaf


def test_sheaf_accepts_compatible_sections() -> None:
    sheaf = Sheaf()
    sheaf.add(LocalSection.create("market", {"state": "calm", "score": 1}))
    sheaf.add(LocalSection.create("market", {"state": "calm", "score": 1, "extra": True}))
    assert sheaf.compatibility() is True
    global_section = sheaf.global_section()
    assert global_section is not None
    assert global_section["market"]["state"] == "calm"


def test_sheaf_rejects_conflicting_sections() -> None:
    sheaf = Sheaf()
    sheaf.add(LocalSection.create("robot", {"mode": "idle"}))
    sheaf.add(LocalSection.create("robot", {"mode": "active"}))
    assert sheaf.compatibility() is False
    assert sheaf.global_section() is None
