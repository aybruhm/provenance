from typing import Any, Callable, Protocol

from ..core.models import Decision, ExecutionResult


class ProvenanceGatewayProtocol(Protocol):
    def guard(
        self,
        action: str | None = None,
        *,
        session_id: str,
        **kwargs,
    ) -> Callable[[Any], Any]: ...

    def execute(
        self,
        action: str,
        parameters: dict,
        *,
        session_id: str | None = None,
        decision: Decision | None = None,
    ) -> ExecutionResult: ...

    async def async_execute(
        self,
        action: str,
        parameters: dict,
        *,
        session_id: str | None = None,
        decision: Decision | None = None,
    ) -> ExecutionResult: ...
