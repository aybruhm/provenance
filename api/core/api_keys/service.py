from uuid import UUID

from core.api_keys.dtos import (
    APIKeyDTO,
    CreateAPIKeyDTO,
    CreatedBy,
    UpdateAPIKeyScopeDTO,
)
from core.api_keys.utils import generate_api_key
from dbs.postgres.api_keys.interfaces import APIKeyDAOInterface, APIKeyDBE


class APIKeyService:
    def __init__(self, api_key_dao: APIKeyDAOInterface):
        self.api_key_dao = api_key_dao

    def _map_dbe_to_dto(self, dbe: APIKeyDBE) -> APIKeyDTO:
        return APIKeyDTO(
            id=str(dbe.id),
            prefix=dbe.prefix,  # type: ignore
            key_hash=dbe.key_hash,  # type: ignore
            scope=str(dbe.scope),  # type: ignore
            created_by=CreatedBy(
                id=str(dbe.user.id),
                username=dbe.user.username,
            ),
            created_at=dbe.created_at.isoformat(),
            updated_at=dbe.updated_at.isoformat(),
        )

    async def _map_dto_to_dbe(self, dto: CreateAPIKeyDTO) -> APIKeyDBE:
        return APIKeyDBE(created_by=dto.user_id, scope=dto.scope_id)

    async def create(self, create_dto: CreateAPIKeyDTO) -> str:
        # Generate API key (full_key, prefix, key_hash)
        full_key, prefix, key_hash = generate_api_key()

        # Map DTO to DBE and set prefix/key_hash
        dbe = await self._map_dto_to_dbe(dto=create_dto)
        dbe.prefix = prefix  # type: ignore
        dbe.key_hash = key_hash  # type: ignore

        return full_key

    async def list(self, tenant_id: UUID, offset: int, limit: int) -> list[APIKeyDTO]:
        api_key_dbes = await self.api_key_dao.list(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
        )
        api_key_dtos = [self._map_dbe_to_dto(dbe=dbe) for dbe in api_key_dbes]
        return api_key_dtos

    async def get_by_prefix(self, prefix: str) -> APIKeyDTO | None:
        api_key_dbe = await self.api_key_dao.get_by_prefix(prefix)
        if not api_key_dbe:
            return None

        api_key_dto = self._map_dbe_to_dto(dbe=api_key_dbe)
        return api_key_dto

    async def update_scope(
        self, api_key_id: UUID, update_dto: UpdateAPIKeyScopeDTO
    ) -> APIKeyDTO | None:
        api_key_dbe = await self.api_key_dao.update_scope(
            id=api_key_id,
            scope=update_dto.scope_id,
        )
        if not api_key_dbe:
            return None

        api_key_dto = self._map_dbe_to_dto(dbe=api_key_dbe)
        return api_key_dto

    async def delete(self, api_key_id: UUID) -> bool:
        await self.api_key_dao.delete(id=api_key_id)
        return True
