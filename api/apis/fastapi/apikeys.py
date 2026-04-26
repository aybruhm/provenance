import traceback
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from apis.fastapi.dtos import (
    APIKeyCreateRequestDTO,
    APIKeyListResponseDTO,
    APIKeyMinimalResponseDTO,
    APIKeyResponseDTO,
    APIKeyUpdateScopeRequestDTO,
)
from core.api_keys.service import APIKeyService
from services.dependencies import get_current_user
from services.exceptions import (
    BadRequestException,
    InternalServerErrorException,
    NotFoundException,
)
from utils.logger_utils import logger


class APIKeyAPIRouter:
    def __init__(self, apikey_service: APIKeyService):
        self.apikey_service = apikey_service

        # Initialize api router
        self.router = APIRouter(
            dependencies=[Depends(get_current_user)],
        )

        # Register routes
        self.router.add_api_route(
            "/",
            self.create_api_key,
            methods=["POST"],
            response_model=APIKeyMinimalResponseDTO,
        )
        self.router.add_api_route(
            "/",
            self.get_apikeys,
            methods=["GET"],
            response_model=APIKeyListResponseDTO,
        )
        self.router.add_api_route(
            "/{prefix}",
            self.get_api_key,
            methods=["GET"],
            response_model=APIKeyResponseDTO,
        )
        self.router.add_api_route(
            "/{key_id}",
            self.update_apikey_scope,
            methods=["PUT"],
            response_model=APIKeyResponseDTO,
        )
        self.router.add_api_route(
            "/{key_id}",
            self.delete_apikey,
            methods=["DELETE"],
            response_model=None,
            status_code=status.HTTP_204_NO_CONTENT,
        )

    async def create_api_key(
        self, request: Request, api_key_create_dto: APIKeyCreateRequestDTO
    ) -> APIKeyMinimalResponseDTO:
        try:
            api_key = await self.apikey_service.create(
                create_dto=api_key_create_dto,
            )
            return APIKeyMinimalResponseDTO(api_key=api_key)
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except Exception as e:
            logger.error(f"Failed to create apikey: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to create apikey")

    async def get_apikeys(
        self,
        request: Request,
        tenant_id: str,
        offset: int = Query(0),
        limit: int = Query(100),
    ) -> APIKeyListResponseDTO:
        try:
            apikeys = await self.apikey_service.list(
                tenant_id=UUID(tenant_id),
                offset=offset,
                limit=limit,
            )
            return APIKeyListResponseDTO(api_keys=apikeys)
        except Exception as e:
            logger.error(f"Failed to get apikeys: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to get apikeys")

    async def get_api_key(self, request: Request, prefix: str) -> APIKeyResponseDTO:
        try:
            api_key = await self.apikey_service.get_by_prefix(
                prefix=prefix,
            )
            if not api_key:
                raise NotFoundException(detail="API key not found")
            return APIKeyResponseDTO(api_key=api_key)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get apikey: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to get apikey")

    async def update_apikey_scope(
        self,
        request: Request,
        key_id: str,
        apikey_update_dto: APIKeyUpdateScopeRequestDTO,
    ) -> APIKeyResponseDTO:
        try:
            api_key = await self.apikey_service.update_scope(
                api_key_id=UUID(key_id),
                update_dto=apikey_update_dto,
            )
            if not api_key:
                raise NotFoundException(detail="API key not found")
            return APIKeyResponseDTO(api_key=api_key)
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to update apikey scope: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to update apikey scope")

    async def delete_apikey(
        self,
        request: Request,
        key_id: str,
    ):
        try:
            api_key = await self.apikey_service.delete(api_key_id=UUID(key_id))
            if not api_key:
                raise NotFoundException(detail="API key not found")
            return
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete apikey: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to delete apikey")
