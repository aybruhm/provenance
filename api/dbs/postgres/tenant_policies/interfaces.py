from abc import ABC, abstractmethod
from uuid import UUID

from dbs.postgres.tenant_policies.dbes import TenantPolicyDBE


class TenantPolicyInterface(ABC):
    @abstractmethod
    async def create_tenant_policy(
        self, tenant_id: UUID, policy_id: UUID
    ) -> TenantPolicyDBE:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant_policy(
        self, tenant_id: UUID, policy_id: UUID
    ) -> TenantPolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def update_tenant_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        active: bool,
    ) -> TenantPolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_tenant_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> None:
        raise NotImplementedError
