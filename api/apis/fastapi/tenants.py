import traceback
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from apis.fastapi.dtos import (
    TenantCreateRequestDTO,
    TenantListResponseDTO,
    TenantResponseDTO,
    TenantUpdateRequestDTO,
)
from core.tenants.service import TenantService
from services.dependencies import get_current_user
from services.exceptions import (
    BadRequestException,
    InternalServerErrorException,
    NotFoundException,
)
from utils.logger_utils import logger


class TenantAPIRouter:
    def __init__(self, tenant_service: TenantService):
        self.tenant_service = tenant_service

        # Initialize api router
        self.router = APIRouter(
            dependencies=[Depends(get_current_user)],
        )

        # Register routes
        self.router.add_api_route(
            "/",
            self.create_tenant,
            methods=["POST"],
            response_model=TenantResponseDTO,
        )
        self.router.add_api_route(
            "/",
            self.get_tenants,
            methods=["GET"],
            response_model=TenantListResponseDTO,
        )
        self.router.add_api_route(
            "/{tenant_id}",
            self.get_tenant,
            methods=["GET"],
            response_model=TenantResponseDTO,
        )
        self.router.add_api_route(
            "/{tenant_id}",
            self.update_tenant,
            methods=["PUT"],
            response_model=TenantResponseDTO,
        )

    async def create_tenant(
        self, request: Request, tenant_create_dto: TenantCreateRequestDTO
    ) -> TenantResponseDTO:
        try:
            tenant = await self.tenant_service.create_tenant(
                user_id=request.state.user_id, create_data=tenant_create_dto
            )
            return TenantResponseDTO(tenant=tenant)
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except Exception as e:
            logger.error(f"Failed to create tenant: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to create tenant")

    async def get_tenants(
        self,
        request: Request,
        offset: int = Query(0),
        limit: int = Query(100),
    ) -> TenantListResponseDTO:
        try:
            tenants = await self.tenant_service.query_tenants(
                user_id=request.state.user_id,
                offset=offset,
                limit=limit,
            )
            return TenantListResponseDTO(tenants=tenants)
        except Exception as e:
            logger.error(f"Failed to get tenants: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to get tenants")

    async def get_tenant(self, request: Request, tenant_id: str) -> TenantResponseDTO:
        try:
            tenant = await self.tenant_service.get_tenant(
                id=UUID(tenant_id),
                user_id=request.state.user_id,
            )
            if not tenant:
                raise NotFoundException(detail="Tenant not found")
            return TenantResponseDTO(tenant=tenant)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get tenant: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to get tenant")

    async def update_tenant(
        self,
        request: Request,
        tenant_id: str,
        tenant_update_dto: TenantUpdateRequestDTO,
    ) -> TenantResponseDTO:
        try:
            tenant = await self.tenant_service.update_tenant(
                id=UUID(tenant_id),
                user_id=request.state.user_id,
                update_data=tenant_update_dto,
            )
            if not tenant:
                raise NotFoundException(detail="Tenant not found")
            return TenantResponseDTO(tenant=tenant)
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to update tenant: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to update tenant")
