import traceback
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from apis.fastapi.dtos import (
    AssignPolicyToTenantRequestDTO,
    DeactivateTenantPolicyRequestDTO,
    PolicyCreateRequestDTO,
    PolicyListResponseDTO,
    PolicyResponseDTO,
    PolicyUpdateRequestDTO,
    TenantPolicyResponseDTO,
)
from core.policy.service import PolicyService
from services.dependencies import get_current_user
from services.exceptions import (
    BadRequestException,
    InternalServerErrorException,
    NotFoundException,
)
from utils.logger_utils import logger


class PolicyAPIRouter:
    def __init__(self, policy_service: PolicyService):
        self.policy_service = policy_service

        # Initialize api router
        self.router = APIRouter(
            dependencies=[Depends(get_current_user)],
        )

        # Register routes
        self.router.add_api_route(
            "/",
            self.create_policy,
            methods=["POST"],
            response_model=PolicyResponseDTO,
        )
        self.router.add_api_route(
            "/",
            self.list_policies,
            methods=["GET"],
            response_model=PolicyListResponseDTO,
        )
        self.router.add_api_route(
            "/{policy_id}/assign",
            self.assign_policy_to_tenant,
            methods=["POST"],
            response_model=TenantPolicyResponseDTO,
        )
        self.router.add_api_route(
            "/{policy_id}/deactivate",
            self.deactivate_tenant_policy,
            methods=["POST"],
        )
        self.router.add_api_route(
            "/{policy_id}",
            self.get_tenant_policy,
            methods=["GET"],
            response_model=TenantPolicyResponseDTO,
        )
        self.router.add_api_route(
            "/{policy_id}",
            self.update_policy,
            methods=["PUT"],
            response_model=PolicyResponseDTO,
        )
        self.router.add_api_route(
            "/{policy_id}",
            self.delete_policy,
            methods=["DELETE"],
            include_in_schema=False,
        )

    async def create_policy(
        self,
        request: Request,
        policy_create_dto: PolicyCreateRequestDTO,
    ):
        try:
            policy = await self.policy_service.create_policy(
                create_dto=policy_create_dto
            )
            return PolicyResponseDTO(policy=policy)
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except Exception as e:
            logger.error(f"Failed to create policy: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to create policy")

    async def list_policies(
        self,
        request: Request,
        tenant_id: UUID = Query(...),
    ):
        try:
            tenant_policies_dtos = await self.policy_service.list_tenant_policies(
                tenant_id=tenant_id,
            )
            return PolicyListResponseDTO(policies=tenant_policies_dtos)
        except Exception as e:
            logger.error(f"Failed to list policies: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to list policies")

    async def assign_policy_to_tenant(
        self,
        request: Request,
        policy_id: UUID,
        assign_dto: AssignPolicyToTenantRequestDTO,
    ):
        try:
            (
                tenant_policy_id,
                policy,
            ) = await self.policy_service.assign_policy_to_tenant(
                tenant_id=assign_dto.tenant_id,
                policy_id=policy_id,
            )
            return TenantPolicyResponseDTO(
                tenant_policy_id=tenant_policy_id,
                policy=policy,
            )
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to assign policy to tenant: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(
                detail="Failed to assign policy to tenant"
            )

    async def deactivate_tenant_policy(
        self,
        request: Request,
        tenant_policy_id: UUID,
        deactivate_dto: DeactivateTenantPolicyRequestDTO,
    ):
        try:
            policy_deactivated = await self.policy_service.deactivate_tenant_policy(
                tenant_policy_id=tenant_policy_id,
                active=deactivate_dto.active,
            )
            return not policy_deactivated
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate policy: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to deactivate policy")

    async def get_tenant_policy(
        self,
        request: Request,
        policy_id: UUID,
        tenant_id: UUID = Query(...),
    ):
        try:
            (
                tenant_policy_id,
                policy,
            ) = await self.policy_service.get_tenant_policy_by_tenant_and_policy(
                policy_id=policy_id,
                tenant_id=tenant_id,
            )
            if not policy or not tenant_policy_id:
                raise NotFoundException(detail="Policy not found")

            return TenantPolicyResponseDTO(
                tenant_policy_id=tenant_policy_id,
                policy=policy,
            )
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to delete policy")

    async def get_policy_by_name(self, request: Request, policy_name: str):
        try:
            policy = await self.policy_service.get_policy_by_name(
                name=policy_name,
            )
            if not policy:
                raise NotFoundException(detail="Policy not found")
            return PolicyResponseDTO(policy=policy)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get policy by name: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to get policy by name")

    async def update_policy(
        self,
        request: Request,
        policy_id: UUID,
        policy_update_dto: PolicyUpdateRequestDTO,
    ):
        try:
            policy = await self.policy_service.update_policy(
                policy_id=policy_id,
                update_dto=policy_update_dto,
            )
            if not policy:
                raise NotFoundException(detail="Policy not found")
            return PolicyResponseDTO(policy=policy)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to delete policy")

    async def delete_policy(
        self,
        request: Request,
        policy_id: UUID,
    ):
        try:
            policy_deleted = await self.policy_service.delete_policy(
                policy_id=policy_id
            )
            return policy_deleted
        except Exception as e:
            logger.error(f"Failed to delete policy: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to delete policy")
