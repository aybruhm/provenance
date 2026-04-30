from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from dbs.postgres.users.dbes import UserDBE


class UserDAOInterface(ABC):
    @abstractmethod
    async def create(self, user_dbe: UserDBE) -> UserDBE:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> UserDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_username(self, username: str) -> UserDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        user_id: UUID,
        values_to_update: Dict[str, Any],
    ) -> UserDBE | None:
        raise NotImplementedError
