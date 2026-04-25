from uuid import UUID

from fastapi import APIRouter, Depends, Request

from apis.fastapi.dtos import (
    Decision,
    EscalationCreateRequestDTO,
    ExecuteRequestDTO,
    ExecuteResponseDTO,
)
from core.audit_events.service import AuditEventService
from core.audit_events.service import utils as audit_utils
from core.escalations.manager import EscalationManager
from core.escalations.service import EscalationService
from core.policy.engine import PolicyEngine
from core.tenants.service import TenantService
from services.dependencies import get_authenticated
from utils.logger_utils import logger


class ExecutionGatewayAPIRouter:
    def __init__(
        self,
        policy_engine: PolicyEngine,
        tenant_service: TenantService,
        audit_service: AuditEventService,
        escalation_manager: EscalationManager,
        escalation_service: EscalationService,
    ):
        self.policy_engine = policy_engine
        self.tenant_service = tenant_service
        self.audit_service = audit_service
        self.escalation_manager = escalation_manager
        self.escalation_service = escalation_service

        # Initialize api router
        self.router = APIRouter(
            dependencies=[Depends(get_authenticated)],
        )

        # Register routes
        self.router.add_api_route(
            "/execute",
            self.execute,
            methods=["POST"],
            response_model=ExecuteResponseDTO,
        )

    async def execute(self, request: Request, execute_request: ExecuteRequestDTO):
        """
        Main gateway endpoint.

        Pipeline:
            1. Load tenant policy
            2. Evaluate policy → ALLOW | BLOCK | ESCALATE
            3. If ESCALATE: hold execution, await human decision (60 s timeout)
            4. Write immutable audit event
            5. Return decision to caller
        """

        tenant = await self.tenant_service.get_tenant(
            id=UUID(execute_request.tenant_id),
            user_id=request.state.user_id,
        )
        if not tenant:
            return ExecuteResponseDTO(
                decision=Decision.BLOCK,  # type: ignore
                reason="Tenant not found",
            )

        scope = getattr(request.state, "scope", None)
        if scope and not execute_request.tenant_policy_id:
            # On sdk requests, set automatically.
            execute_request.tenant_policy_id = str(scope)

        if not scope and not execute_request.tenant_policy_id:
            # On api requests, tenant_policy_id is required.
            return ExecuteResponseDTO(
                decision=Decision.BLOCK,  # type: ignore
                reason="tenant_policy_id is required",
            )

        if not execute_request.tenant_policy_id:
            return ExecuteResponseDTO(
                decision=Decision.BLOCK,  # type: ignore
                reason="tenant_policy_id is required",
            )

        policy = await self.policy_engine.load_policy(
            tenant_policy_id=execute_request.tenant_policy_id
        )
        parameters = execute_request.parameters or dict()
        decision, reason = self.policy_engine.evaluate_policy(
            policy=policy,
            action=execute_request.action,
            parameters=parameters,
        )

        escalation_id: str | None = None
        actor_human_id: str | None = None
        final_decision = decision

        # ── BLOCK: immediate reject, no escalation ────────────────────────────────
        if decision == "BLOCK":
            execute_request.decision = "BLOCK"
            event = await self.audit_service.create_audit_event(
                create_data=execute_request
            )
            return ExecuteResponseDTO(
                event_id=str(event.id),
                decision=event.decision,  # type: ignore
                reason=reason,
            )

        # ── ESCALATE: hold until human decision ───────────────────────────────────
        if decision == "ESCALATE":
            payload_hash = audit_utils.hash_payload(payload=parameters)
            escalation_create_data = EscalationCreateRequestDTO(
                tenant_id=UUID(execute_request.tenant_id),
                agent_id=UUID(execute_request.agent_id),
                action=execute_request.action,
                parameters_hash=payload_hash,
            )
            escalation = await self.escalation_service.create_escalation(
                create_data=escalation_create_data
            )
            escalation_id = str(escalation.id)

            logger.info(
                f"\n  ESCALATION  id={escalation_id}\n"
                f"   action={execute_request.action}  reason={reason}\n"
                f"   → POST /v1/escalations/{escalation_id}/decide\n"
            )

            # Execution is held here until operator resolves or timeout fires.
            # asyncio.wait_for yields to the event loop so approve requests
            # can be served concurrently by the same uvicorn worker pool.
            (
                human_decision,
                approver_id,
            ) = await self.escalation_manager.wait_for_decision(
                escalation_id=escalation_id,
                timeout_seconds=60,
            )

            if human_decision == "APPROVE":
                final_decision = "ALLOW"
                actor_human_id = approver_id
                reason = f"Escalation APPROVED by {approver_id}"
            else:
                final_decision = "BLOCK"
                reason = f"Escalation {human_decision} — action blocked"

        # ── write audit event (ALLOW or resolved escalation) ─────────────────────
        audit_create_data = ExecuteRequestDTO(
            session_id=execute_request.session_id,
            agent_id=execute_request.agent_id,
            tenant_id=execute_request.tenant_id,
            tenant_policy_id=execute_request.tenant_policy_id,
            action=execute_request.action,
            parameters=execute_request.parameters,
            decision=final_decision,
            escalation_id=escalation_id,
            actor_human_id=actor_human_id,
        )
        event = await self.audit_service.create_audit_event(
            create_data=audit_create_data
        )

        return ExecuteResponseDTO(
            event_id=str(event.id),
            decision=final_decision,  # type: ignore[arg-type]
            reason=reason,
            escalation_id=escalation_id,
            actor_human_id=actor_human_id,
        )
