from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.sql.elements import ColumnElement

from dbs.postgres.tenants.dbes import TenantDBE


class TenantDAOInterface(ABC):
    @abstractmethod
    async def create(self, name: str, policy_id: str) -> TenantDBE:
        raise NotImplementedError

    @abstractmethod
    async def get(self, id: UUID) -> TenantDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        id: UUID,
        values_to_update: Dict[str, Any],
    ) -> TenantDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def query(
        self,
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[TenantDBE]:
        raise NotImplementedError
