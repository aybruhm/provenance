from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from dbs.postgres.policy.dbes import PolicyDBE


class PolicyDAOInterface(ABC):
    @abstractmethod
    async def create_policy(self, policy_dbe: PolicyDBE) -> PolicyDBE:
        raise NotImplementedError

    @abstractmethod
    async def get_policy(self, policy_id: UUID) -> PolicyDBE | None:
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
