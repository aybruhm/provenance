from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from apis.fastapi.dtos import (
    AuditEventIntegrityResponseDTO,
    AuditEventResponseDTO,
)
from core.audit_events.service import AuditEventService
from services.dependencies import get_authenticated


class AuditAPIRouter:
    def __init__(self, audit_service: AuditEventService):
        self.audit_service = audit_service

        # Initialize api router
        self.router = APIRouter(
            dependencies=[Depends(get_authenticated)],
        )

        # Register routes
        self.router.add_api_route(
            "/{tenant_id}",
            self.get_audit,
            methods=["GET"],
            response_model=AuditEventResponseDTO,
        )
        self.router.add_api_route(
            "/integrity/{tenant_id}",
            self.integrity_scan,
            methods=["GET"],
            response_model=AuditEventIntegrityResponseDTO,
        )

    async def get_audit(
        self,
        request: Request,
        tenant_id: str,
        limit: int = Query(default=100, le=10_000),
    ):
        audit_logs = await self.audit_service.list_audit_events(
            tenant_id=UUID(tenant_id),
            limit=limit,
        )
        return AuditEventResponseDTO(events=audit_logs)

    async def integrity_scan(
        self,
        request: Request,
        tenant_id: str,
        limit: int = Query(default=10_000, le=10_000),
    ):
        """
        Run a full hash-chain integrity scan for a tenant's audit log.

        Note: in production, this would likely be an offline batch job rather than an API endpoint.
        """

        chain_integrity = await self.audit_service.verify_chain_integrity(
            tenant_id=UUID(tenant_id),
            limit=limit,
        )
        return AuditEventIntegrityResponseDTO(integrity=chain_integrity)
