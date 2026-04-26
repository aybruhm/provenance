import logging
import uuid
import warnings
from typing import Any

import httpx

from .models import Decision, ExecutionResult

log = logging.getLogger(f"sdk.{__name__}")


class ProvenanceClient:
    """
    ProvenanceClient is the single entry point for all SDK interactions.

    Usage patterns
    ──────────────
    1. Direct execute (most explicit):

        result = provenance.execute("payments.initiate", {"amount": 50, "currency": "GBP"})

    2. Decorator — wraps any sync or async callable transparently:

        @provenance.guard("payments.initiate")
        def initiate_payment(amount: float, currency: str, recipient_id: str) -> dict:
            return payment_service.create(amount, currency, recipient_id)

        # Call it like normal — Provenance intercepts before the function runs.
        result = initiate_payment(amount=50, currency="GBP", recipient_id="rec_123")

    3. Session context manager — groups related calls under one session_id:

        with provenance.session("sess_checkout_flow") as sess:
            sess.execute("payments.initiate", {...})
            sess.execute("email.send", {...})
    """

    def __init__(
        self,
        *,
        gateway_url: str,
        agent_id: str,
        on_gateway_error: str = "closed",
        default_session: str | None = None,
        timeout: float = 90.0,
        api_key: str | None = None,
    ) -> None:
        """
        Args:
            gateway_url (str):        base URL of the Provenance gateway  (e.g. "http://localhost:8000")
            agent_id (str):           the agent identity making tool calls
            on_gateway_error (str):   "closed" | "open"  — how to handle gateway unavailability
            default_session (str | None): shared session_id for all calls; auto-generated if omitted
            timeout (float):          HTTP request timeout in seconds (escalations need a high value)
            api_key (str | None):     API key for authentication; sent as an X-PROVENANCE-API-KEY header on every request
        """

        self.gateway_url = gateway_url.rstrip("/")
        self.agent_id = agent_id
        self.on_gateway_error = on_gateway_error
        self.default_session = default_session or f"sess_{uuid.uuid4().hex[:16]}"
        self.timeout = timeout
        self.api_key = api_key

        # Reusable sync/async HTTP clients (lazy-init)
        self._sync_client: httpx.Client | None = None
        self._async_client: httpx.AsyncClient | None = None

        # Thread-safety locks for HTTP client initialization
        self._sync_client_lock = __import__("threading").Lock()
        self._async_client_lock = __import__("asyncio").Lock()

    # ── HTTP clients ──────────────────────────────────────────────────────────

    def _auth_headers(self) -> dict[str, str]:
        if self.api_key:
            return {"X-PROVENANCE-API-KEY": f"{self.api_key}"}
        return {}

    def _http(self) -> httpx.Client:
        with self._sync_client_lock:
            if self._sync_client is None or self._sync_client.is_closed:
                self._sync_client = httpx.Client(
                    base_url=self.gateway_url,
                    headers=self._auth_headers(),
                    timeout=self.timeout,
                    trust_env=False,
                )
            return self._sync_client

    async def _ahttp(self) -> httpx.AsyncClient:
        async with self._async_client_lock:
            if self._async_client is None or self._async_client.is_closed:
                self._async_client = httpx.AsyncClient(
                    base_url=self.gateway_url,
                    headers=self._auth_headers(),
                    timeout=self.timeout,
                    trust_env=False,
                )
            return self._async_client

    def close(self) -> None:
        if self._sync_client:
            self._sync_client.close()

    async def aclose(self) -> None:
        if self._async_client:
            await self._async_client.aclose()

    # ── low-level request builders ────────────────────────────────────────────

    def _build_payload(
        self,
        action: str,
        parameters: dict[str, Any],
        session_id: str,
        decision: Decision | None = None,
    ) -> dict:
        return dict(
            session_id=session_id,
            agent_id=self.agent_id,
            action=action,
            decision=decision or Decision.BLOCK,
            parameters=parameters,
        )

    @staticmethod
    def _parse_response(data: dict, action: str) -> ExecutionResult:
        return ExecutionResult(
            decision=Decision(data["decision"]),
            reason=data.get("reason", ""),
            action=action,
            event_id=data.get("event_id", ""),
            escalation_id=data.get("escalation_id"),
            actor_human_id=data.get("actor_human_id"),
        )

    def _fail_open(self, action: str, exc: Exception) -> ExecutionResult:
        warnings.warn(
            f"Provenance gateway unreachable ({exc}); failing open for '{action}'",
            stacklevel=4,
        )
        return ExecutionResult(
            decision=Decision.ALLOW,
            reason="Gateway unavailable — fail-open policy applied",
            action=action,
            event_id="",
        )
