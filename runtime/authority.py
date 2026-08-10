from __future__ import annotations

from enum import Enum


class AuthorityViolation(PermissionError):
    """Raised when an informational result is used as runtime authority."""


class AuthorityLevel(str, Enum):
    CONTEXT = "context"
    SHADOW = "shadow"
    DIAGNOSTIC = "diagnostic"
    PREDICTIVE = "predictive"
    RUNTIME = "runtime"


def require_runtime_authority(level: AuthorityLevel) -> None:
    if level is not AuthorityLevel.RUNTIME:
        raise AuthorityViolation(f"{level.value} output has no runtime authority")
