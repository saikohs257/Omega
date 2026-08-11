from __future__ import annotations

from dataclasses import dataclass, replace

from runtime.experiment_result import ExperimentResult


class TestSpineViolation(PermissionError):
    """Raised when adaptive components attempt to access the locked test spine."""
    __test__ = False


@dataclass(frozen=True, slots=True)
class TestSpine:
    __test__ = False
    spine_id: str
    locked: bool = True
    result_ids: tuple[str, ...] = ()

    def read(self, requester: str) -> None:
        if self.locked and requester in {"end", "pond", "oracle_mutation", "diagnostic_tuner"}:
            raise TestSpineViolation(f"{requester} cannot access locked test spine {self.spine_id}")
        return None

    def accept(self, result: ExperimentResult) -> "TestSpine":
        """Return a new spine containing only an explicitly test-scoped result."""
        try:
            result.assert_test_eligible()
        except ValueError as exc:
            raise TestSpineViolation(str(exc)) from exc
        if result.result_id in self.result_ids:
            return self
        return replace(self, result_ids=self.result_ids + (result.result_id,))
