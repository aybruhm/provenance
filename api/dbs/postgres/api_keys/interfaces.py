from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from dbs.postgres.api_keys.dbes import APIKeyDBE


class APIKeyDAOInterface(ABC):
    @abstractmethod
    async def create(self, api_key: APIKeyDBE) -> APIKeyDBE:
        raise NotImplementedError

    @abstractmethod
    async def query(
        self, filters: list[Any], offset: int, limit: int
    ) -> list[APIKeyDBE]:
        raise NotImplementedError

    @abstractmethod
    async def list(self, tenant_id: UUID, offset: int, limit: int) -> list[APIKeyDBE]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_prefix(self, prefix: str) -> APIKeyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def update_scope(self, id: UUID, scope: UUID) -> APIKeyDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: UUID) -> None:
        raise NotImplementedError
