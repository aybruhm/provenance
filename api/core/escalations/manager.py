from __future__ import annotations

import asyncio
from typing import OrderedDict
from uuid import UUID

from core.escalations.dtos import CreateEscalationDTO, UpdateEscalationDTO
from core.escalations.service import EscalationService

# ── in-memory hold registry ───────────────────────────────────────────────────


class _Hold:
    __slots__ = ("event", "decision", "approver_id")

    def __init__(self) -> None:
        self.event: asyncio.Event = asyncio.Event()
        self.decision: str | None = None
        self.approver_id: str | None = None


# ── escalation orchestrator ───────────────────────────────────────────────────


class EscalationManager:
    """
    Escalation Manager manages the lifecycle of an escalation from creation to resolution.

    When a policy returns ESCALATE, the Execution Gateway:
      1. Creates an escalation record (DB + in-memory asyncio.Event)
      2. Awaits the event with a configurable timeout
      3. An operator calls POST /v1/escalations/{id}/decide to unblock it

    !NOTE: In production this hold would be a durable Temporal workflow state.
    """

    def __init__(self, service: EscalationService):
        self.service = service
        self._holds: dict[str, _Hold] = OrderedDict()

    # ── create ────────────────────────────────────────────────────────────────────

    async def create_escalation(
        self,
        *,
        tenant_id: str,
        agent_id: str,
        action: str,
        parameters_hash: str,
    ) -> str:
        escalation = await self.service.create_escalation(
            create_data=CreateEscalationDTO(
                tenant_id=UUID(tenant_id),
                agent_id=UUID(agent_id),
                action=action,
                parameters_hash=parameters_hash,
                status="PENDING",
            )
        )
        escalation_id = str(escalation.id)

        self._holds[escalation_id] = _Hold()
        return escalation_id

    # ── wait ──────────────────────────────────────────────────────────────────────

    async def wait_for_decision(
        self,
        *,
        escalation_id: str,
        timeout_seconds: int = 60,
    ) -> tuple[str, str | None]:
        """
        Block until an operator resolves the escalation (or timeout fires).

        Returns:
            (decision, approver_id)  where decision ∈ {"APPROVE", "REJECT", "TIMEOUT"}
        """

        hold = self._holds.get(escalation_id)
        if not hold:
            return "TIMEOUT", None

        try:
            await asyncio.wait_for(hold.event.wait(), timeout=timeout_seconds)
            decision = hold.decision or "TIMEOUT"
            approver_id = hold.approver_id
        except asyncio.TimeoutError:
            decision = "TIMEOUT"
            approver_id = None
            await self.service.update_escalation(
                id=UUID(escalation_id),
                update_data=UpdateEscalationDTO(status="TIMEOUT"),
            )
        finally:
            self._holds.pop(escalation_id, None)

        return decision, approver_id

    # ── resolve ───────────────────────────────────────────────────────────────────

    async def resolve_escalation(
        self,
        *,
        escalation_id: str,
        decision: str,
        approver_id: str,
        reason: str | None = None,
    ) -> bool:
        """
        Called by the /decide endpoint.  Unblocks the waiting execute handler.

        Returns False if escalation_id not found or already resolved.
        """

        hold = self._holds.get(escalation_id)
        if not hold:
            return False

        hold.decision = decision
        hold.approver_id = approver_id

        # Write to DB before setting the event so the execute handler
        # can immediately read the resolved state from the database.
        await self.service.update_escalation(
            id=UUID(escalation_id),
            update_data=UpdateEscalationDTO(
                status="TIMEOUT",
                approver_id=approver_id,
                reason=reason,
            ),
        )

        hold.event.set()
        return True
