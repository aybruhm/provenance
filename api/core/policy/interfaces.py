from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from dbs.postgres.policy.dbes import PolicyDBE
from dbs.postgres.tenant_policies.dbes import TenantPolicyDBE


class PolicyDAOInterface(ABC):
    @abstractmethod
    async def create_policy(self, policy_dbe: PolicyDBE) -> PolicyDBE:
        raise NotImplementedError

    @abstractmethod
    async def get_policy(self, policy_id: UUID) -> PolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def get_policy_by_name(self, name: str) -> PolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def update_policy(
        self,
        policy_id: UUID,
        values_to_update: Dict[str, Any],
    ) -> PolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_policy(self, policy_id: UUID) -> None:
        raise NotImplementedError


class TenantPolicyInterface(ABC):
    @abstractmethod
    async def create_tenant_policy(
        self, tenant_id: UUID, policy_id: UUID
    ) -> TenantPolicyDBE:
        raise NotImplementedError

    @abstractmethod
    async def list_tenant_policies(self, tenant_id: UUID) -> list[TenantPolicyDBE]:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant_policy(self, tenant_policy_id: UUID) -> TenantPolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant_policy_by_tenant_and_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> TenantPolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def update_tenant_policy(
        self, tenant_policy_id: UUID, active: bool
    ) -> TenantPolicyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_tenant_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> None:
        raise NotImplementedError
