from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apis.fastapi.dtos import (
    EscalationDecisionRequestDTO,
    EscalationDecisionResponseDTO,
    EscalationResponseDTO,
)
from core.escalations.manager import EscalationManager
from core.escalations.service import EscalationService
from services.dependencies import get_current_user
from utils.logger_utils import logger


class EscalationAPIRouter:
    def __init__(
        self,
        escalation_service: EscalationService,
        escalation_manager: EscalationManager,
    ):
        self.escalation_service = escalation_service
        self.escalation_manager = escalation_manager

        # Initialize api router
        self.router = APIRouter(
            dependencies=[Depends(get_current_user)],
        )

        # Register routes
        self.router.add_api_route(
            "/",
            self.list_escalations,
            methods=["GET"],
            response_model=EscalationResponseDTO,
        )
        self.router.add_api_route(
            "/pending",
            self.list_pending_escalations,
            methods=["GET"],
            response_model=EscalationResponseDTO,
        )
        self.router.add_api_route(
            "/{escalation_id}/decide",
            self.decide_escalation,
            methods=["POST"],
        )

    async def decide_escalation(
        self,
        request: Request,
        escalation_id: str,
        escalation_request: EscalationDecisionRequestDTO,
    ):
        """
        Human approver resolves a pending escalation.
        """

        if escalation_request.decision not in ("APPROVE", "REJECT"):
            raise HTTPException(
                status_code=400,
                detail={"message": "Invalid decision. Use: APPROVE | REJECT"},
            )

        resolved = await self.escalation_manager.resolve_escalation(
            escalation_id=escalation_id,
            decision=escalation_request.decision,
            approver_id=escalation_request.approver_id,
            reason=escalation_request.reason,
        )
        if not resolved:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"Escalation '{escalation_id}' not found or already resolved"
                },
            )

        logger.info(
            f"\n{'[>/]' if escalation_request.decision == 'APPROVE' else '❌'}  Escalation {escalation_request.decision}"
            f"  id={escalation_id}  approver={escalation_request.approver_id}\n"
        )
        return EscalationDecisionResponseDTO(
            escalation_id=escalation_id,
            decision=escalation_request.decision,
            approver_id=escalation_request.approver_id,
            reason=escalation_request.reason,
        )

    async def list_pending_escalations(
        self,
        request: Request,
        tenant_id: str = Query(...),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=10_000),
    ):
        pending_escalations = await self.escalation_service.list_escalations(
            tenant_id=UUID(tenant_id),
            offset=offset,
            limit=limit,
            status="PENDING",
        )
        return EscalationResponseDTO(escalations=pending_escalations)

    async def list_escalations(
        self,
        request: Request,
        tenant_id: str = Query(...),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, le=10_000),
    ):
        escalations = await self.escalation_service.list_escalations(
            tenant_id=UUID(tenant_id),
            offset=offset,
            limit=limit,
        )
        return EscalationResponseDTO(escalations=escalations)
