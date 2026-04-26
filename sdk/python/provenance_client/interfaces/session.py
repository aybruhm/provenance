from typing import Any, Callable, Protocol

from ..core.models import Decision, ExecutionResult


class ProvenanceSessionProtocol(Protocol):
    def guard(
        self,
        action: str | None = None,
        **kwargs,
    ) -> Callable[[Any], Any]: ...

    def execute(
        self,
        action: str,
        parameters: dict,
        *,
        decision: Decision | None = None,
    ) -> ExecutionResult: ...

    async def async_execute(
        self,
        action: str,
        parameters: dict,
        *,
        decision: Decision | None = None,
    ) -> ExecutionResult: ...

    def __enter__(self) -> "ProvenanceSessionProtocol": ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...
