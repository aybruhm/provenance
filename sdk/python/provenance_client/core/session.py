import logging
from typing import Any, Callable, TypeVar

from ..interfaces import ProvenanceGatewayProtocol, ProvenanceSessionProtocol
from .models import Decision, ExecutionResult

F = TypeVar("F", bound=Callable[..., Any])
log = logging.getLogger(f"sdk.{__name__}")


class ProvenanceSession(ProvenanceSessionProtocol):
    """
    Scopes a series of tool-call executions to a shared session_id.

    Supports use as a sync context manager.  For async, use async with directly on the ProvenanceClient and pass session_id= explicitly.
    """

    def __init__(
        self,
        gateway: ProvenanceGatewayProtocol,
        session_id: str,
    ) -> None:
        self._gateway = gateway
        self.session_id = session_id
        self._results: list[ExecutionResult] = []

    # ── execute variants ──────────────────────────────────────────────────────

    def execute(
        self,
        action: str,
        parameters: dict[str, Any],
        *,
        decision: Decision | None = None,
    ) -> ExecutionResult:
        result = self._gateway.execute(
            action,
            parameters,
            session_id=self.session_id,
            decision=decision,  # type: ignore
        )
        self._results.append(result)  # type: ignore
        return result

    async def async_execute(
        self,
        action: str,
        parameters: dict[str, Any],
        *,
        decision: Decision | None = None,
    ) -> ExecutionResult:
        result = await self._gateway.async_execute(
            action,
            parameters,
            session_id=self.session_id,
            decision=decision,
        )
        self._results.append(result)  # type: ignore
        return result

    # ── guard scoped to this session ──────────────────────────────────────────

    def guard(self, action: str | None = None, **kwargs) -> Callable[[F], F]:
        """Same as ProvenanceClient.guard() but pins session_id to this session."""
        return self._gateway.guard(action, session_id=self.session_id, **kwargs)

    # ── session summary ───────────────────────────────────────────────────────

    @property
    def results(self) -> list[ExecutionResult]:
        return list(self._results)

    @property
    def blocked_count(self) -> int:
        return sum(1 for r in self._results if r.blocked)

    @property
    def allowed_count(self) -> int:
        return sum(1 for r in self._results if r.allowed)

    # ── context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "ProvenanceSession":
        return self

    def __exit__(self, *_) -> None:
        log.info(
            f"Session {self.session_id!r} completed with {len(self._results)} results"
        )

    def __repr__(self) -> str:
        return (
            f"ProvenanceSession(id={self.session_id!r}, results={len(self._results)})"
        )
