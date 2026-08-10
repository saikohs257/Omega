import pytest

from runtime.authority import AuthorityLevel, AuthorityViolation, require_runtime_authority


def test_context_cannot_become_runtime_authority() -> None:
    with pytest.raises(AuthorityViolation):
        require_runtime_authority(AuthorityLevel.CONTEXT)


def test_shadow_cannot_become_runtime_authority() -> None:
    with pytest.raises(AuthorityViolation):
        require_runtime_authority(AuthorityLevel.SHADOW)


def test_runtime_authority_is_explicit() -> None:
    assert require_runtime_authority(AuthorityLevel.RUNTIME) is None
