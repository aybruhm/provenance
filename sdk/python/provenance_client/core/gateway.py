import asyncio
import functools
import inspect
import logging
import uuid
from typing import Any, Callable, TypeVar

import httpx

from ..interfaces.gateway import ProvenanceGatewayProtocol
from ..services import GatewayError, PolicyBlockedError
from .client import ProvenanceClient
from .models import Decision, ExecutionResult
from .session import ProvenanceSession

log = logging.getLogger(f"sdk.{__name__}")
F = TypeVar("F", bound=Callable[..., Any])


_PROVENANCE_ATTR = "_provenance_guarded"


class ProvenanceGateway(ProvenanceGatewayProtocol):
    def __init__(self, client: ProvenanceClient):
        self._client = client

    def __repr__(self) -> str:
        return (
            f"ProvenanceGateway(cl={self._client.gateway_url!r}, "
            f"tenant={self._client.tenant_id!r}, agent={self._client.agent_id!r}, tenant_policy_id={self._client.tenant_policy_id!r})"
        )

    def execute(
        self,
        action: str,
        parameters: dict[str, Any],
        *,
        session_id: str | None = None,
        decision: Decision | None = None,
    ) -> ExecutionResult:
        """
        Synchronous policy evaluation.

        Raises:
            PolicyBlockedError if decision is BLOCK.
            GatewayError if gateway unreachable and on_gateway_error='closed'.
        """

        sid = session_id or self._client.default_session
        payload = self._client._build_payload(
            action=action,
            parameters=parameters,
            session_id=sid,
            decision=decision,
        )
        try:
            resp = self._client._http().post(
                "/v1/gateway/execute",
                json=payload,
            )
            resp.raise_for_status()
            result = self._client._parse_response(resp.json(), action)
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
        ) as exc:
            if self._client.on_gateway_error == "open":
                return self._client._fail_open(action=action, exc=exc)
            raise GatewayError(self._client.gateway_url, exc) from exc

        if result.blocked:
            raise PolicyBlockedError(action, result.reason, result.event_id)
        return result

    async def async_execute(
        self,
        action: str,
        parameters: dict[str, Any],
        *,
        session_id: str | None = None,
        decision: Decision | None = None,
    ) -> ExecutionResult:
        """
        Asynchronous policy evaluation.

        Raises:
            PolicyBlockedError if decision is BLOCK.
            GatewayError if gateway unreachable and on_gateway_error='closed'.
        """

        sid = session_id or self._client.default_session
        payload = self._client._build_payload(
            action=action,
            parameters=parameters,
            session_id=sid,
            decision=decision,
        )
        try:
            http_client = await self._client._ahttp()
            resp = await http_client.post(
                "/v1/gateway/execute",
                json=payload,
            )
            resp.raise_for_status()
            result = self._client._parse_response(resp.json(), action)
        except (
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.HTTPStatusError,
        ) as exc:
            if self._client.on_gateway_error == "open":
                return self._client._fail_open(action=action, exc=exc)
            raise GatewayError(self._client.gateway_url, exc) from exc

        if result.blocked:
            raise PolicyBlockedError(action, result.reason, result.event_id)
        return result

    # ── decorator: @provenance.guard ────────────────────────────────────────────

    def guard(  # type: ignore[override]
        self,
        action: str | None = None,
        *,
        session_id: str | None = None,
        decision: Decision | None = None,
        raise_on_block: bool = True,
    ) -> Callable[[F], F]:
        """
        Decorator that gates any callable behind Provenance policy evaluation.

        Args:
            action (str | None): The action name to use for policy evaluation. Defaults to "<module>.<qualname>" if not supplied.
            session_id (str | None): The session ID to use for policy evaluation. Defaults to a new session ID if not supplied.
            decision (Decision | None): The decision to use for policy evaluation. Defaults to None (use the policy's default decision).
            raise_on_block (bool): Whether to raise a PolicyBlockedError if the policy blocks execution. Defaults to True.

        Example:
            @provenance.guard("payments.initiate")
            async def initiate_payment(amount: float, currency: str) -> dict:
                return await payment_service.create(amount, currency)
        """

        def decorator(func: F) -> F:
            resolved_action = action or f"{func.__module__}.{func.__qualname__}"
            sig = inspect.signature(func)

            def _extract_params(*args, **kwargs) -> dict[str, Any]:
                """Bind call-site args to parameter names for the audit log."""
                try:
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                    return {
                        k: v
                        for k, v in bound.arguments.items()
                        if not k.startswith("_")  # skip private/internal args
                    }
                except TypeError:
                    return kwargs  # fallback: just pass whatever kwargs exist

            # ── sync wrapper ──────────────────────────────────────────────────
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                params = _extract_params(*args, **kwargs)
                try:
                    result = self.execute(
                        resolved_action,
                        params,
                        session_id=session_id,
                        decision=decision,
                    )
                except PolicyBlockedError:
                    if raise_on_block:
                        raise
                    return None

                tool_result = func(*args, **kwargs)
                result.tool_result = tool_result
                return tool_result

            # ── async wrapper ─────────────────────────────────────────────────
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                params = _extract_params(*args, **kwargs)
                try:
                    result = await self.async_execute(
                        resolved_action,
                        params,
                        session_id=session_id,
                        decision=decision,
                    )
                except PolicyBlockedError:
                    if raise_on_block:
                        raise
                    return None

                tool_result = await func(*args, **kwargs)
                result.tool_result = tool_result
                return tool_result

            wrapper = (
                async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
            )
            # Tag for introspection
            setattr(wrapper, _PROVENANCE_ATTR, True)
            setattr(wrapper, "_provenance_action", resolved_action)
            return wrapper  # type: ignore[return-value]

        return decorator

    # ── session context manager ───────────────────────────────────────────────

    def session(self, session_id: str | None = None) -> "ProvenanceSession":
        """
        Return a ProvenanceSession context manager that scopes all calls to
        a single session_id.

        with provenance.session("sess_checkout") as sess:
            sess.execute("payments.initiate", {...})
            sess.execute("email.send", {...})
        """
        return ProvenanceSession(self, session_id or f"sess_{uuid.uuid4().hex[:16]}")
