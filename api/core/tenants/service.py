from uuid import UUID

from core.tenants.dtos import CreateTenantDTO, TenantDTO, UpdateTenantDTO
from dbs.postgres.tenants.dbes import TenantDBE
from dbs.postgres.tenants.interfaces import TenantDAOInterface


class TenantService:
    def __init__(self, tenant_dao: TenantDAOInterface):
        self.tenant_dao = tenant_dao

    def _map_dbe_to_dto(self, dbe: TenantDBE) -> TenantDTO:
        return TenantDTO(
            id=dbe.id,  # type: ignore
            name=dbe.name,  # type: ignore
            policy_id=dbe.policy_id,  # type: ignore
            created_at=dbe.created_at,  # type: ignore
            updated_at=dbe.updated_at,  # type: ignore
        )

    async def create_tenant(
        self, user_id: UUID, create_data: CreateTenantDTO
    ) -> TenantDTO:
        tenant_dbe = await self.tenant_dao.create(
            name=create_data.name,
            policy_id=create_data.policy_id,
            user_id=user_id,
        )
        tenant_dto = self._map_dbe_to_dto(dbe=tenant_dbe)
        return tenant_dto

    async def get_tenant(self, id: UUID, user_id: UUID) -> TenantDTO | None:
        tenant_dbe = await self.tenant_dao.get(id=id, user_id=user_id)
        if not tenant_dbe:
            return None
        tenant_dto = self._map_dbe_to_dto(dbe=tenant_dbe)
        return tenant_dto

    async def update_tenant(
        self,
        id: UUID,
        user_id: UUID,
        update_data: UpdateTenantDTO,
    ) -> TenantDTO | None:
        tenant_dbe = await self.tenant_dao.update(
            id=id,
            user_id=user_id,
            values_to_update=update_data.model_dump(
                exclude_none=True,
            ),
        )
        if not tenant_dbe:
            return None
        tenant_dto = self._map_dbe_to_dto(dbe=tenant_dbe)
        return tenant_dto

    async def query_tenants(
        self,
        user_id: UUID,
        offset: int,
        limit: int,
    ) -> list[TenantDTO]:
        filters = []
        tenants_dbes = await self.tenant_dao.query(
            user_id=user_id,
            filters=filters,
            offset=offset,
            limit=limit,
        )
        tenants_dtos = [self._map_dbe_to_dto(dbe=tenant) for tenant in tenants_dbes]
        return tenants_dtos
