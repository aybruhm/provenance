from uuid import UUID

from core.policy.dtos import CreatePolicyDTO, PolicyDTO, UpdatePolicyDTO
from dbs.postgres.policy.dbes import PolicyDBE
from dbs.postgres.policy.interfaces import PolicyDAOInterface
from dbs.postgres.tenant_policies.dbes import TenantPolicyDBE
from dbs.postgres.tenant_policies.interfaces import TenantPolicyInterface


class PolicyService:
    def __init__(
        self,
        dao: PolicyDAOInterface,
        tenant_policy_dao: TenantPolicyInterface,
    ):
        self.dao = dao
        self.tenant_policy_dao = tenant_policy_dao

    def _map_dto_to_dbe(self, dto: CreatePolicyDTO | UpdatePolicyDTO) -> PolicyDBE:
        return PolicyDBE(
            name=dto.name,
            description=dto.description,
            rules={"rules": [rule.model_dump() for rule in dto.rules]},
        )

    def _map_dbe_to_dto(self, dbe: PolicyDBE) -> PolicyDTO:
        return PolicyDTO(
            id=str(dbe.id),
            name=dbe.name,  # type: ignore
            version=dbe.version,  # type: ignore
            description=dbe.description,  # type: ignore
            rules=dbe.rules.get("rules", []),
            created_at=dbe.created_at,  # type: ignore
            updated_at=dbe.updated_at,  # type: ignore
        )

    def _map_tenant_policy_dbe_to_dto(self, dbe: TenantPolicyDBE) -> PolicyDTO:
        return PolicyDTO(
            id=str(dbe.policy_id),
            name=dbe.policy.name,  # type: ignore
            version=dbe.policy.version,  # type: ignore
            description=dbe.policy.description,  # type: ignore
            rules=dbe.policy.rules.get("rules", []),  # type: ignore
            created_at=dbe.policy.created_at,  # type: ignore
            updated_at=dbe.policy.updated_at,  # type: ignore
        )

    async def create_policy(self, create_dto: CreatePolicyDTO) -> PolicyDTO:
        dbe = self._map_dto_to_dbe(create_dto)
        policy_dbe = await self.dao.create_policy(policy_dbe=dbe)
        policy_dto = self._map_dbe_to_dto(dbe=policy_dbe)
        return policy_dto

    async def get_tenant_policy(self, tenant_policy_id: UUID) -> PolicyDTO | None:
        tenant_policy = await self.tenant_policy_dao.get_tenant_policy(
            tenant_policy_id=tenant_policy_id
        )
        if not tenant_policy:
            return None

        tenant_policy_dto = self._map_tenant_policy_dbe_to_dto(dbe=tenant_policy)
        return tenant_policy_dto

    async def get_policy(self, policy_id: UUID) -> PolicyDTO | None:
        policy_dbe = await self.dao.get_policy(policy_id=policy_id)
        if not policy_dbe:
            return None

        policy_dto = self._map_dbe_to_dto(dbe=policy_dbe)
        return policy_dto

    async def get_policy_by_name(self, name: str) -> PolicyDTO | None:
        policy_dbe = await self.dao.get_policy_by_name(name=name)
        if not policy_dbe:
            return None

        policy_dto = self._map_dbe_to_dto(dbe=policy_dbe)
        return policy_dto

    async def update_policy(
        self, policy_id: UUID, update_dto: UpdatePolicyDTO
    ) -> PolicyDTO | None:
        policy_dbe = await self.dao.update_policy(
            policy_id=policy_id,
            values_to_update=update_dto.model_dump(),
        )
        if not policy_dbe:
            return None

        policy_dto = self._map_dbe_to_dto(dbe=policy_dbe)
        return policy_dto

    async def delete_policy(self, policy_id: UUID) -> bool:
        await self.dao.delete_policy(policy_id=policy_id)
        return True
