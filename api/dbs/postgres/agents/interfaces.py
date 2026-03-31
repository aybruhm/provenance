from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.sql.elements import ColumnElement

from dbs.postgres.agents.dbes import AgentDBE


class AgentDAOInterface(ABC):
    @abstractmethod
    async def create(
        self,
        name: str,
        tenant_id: UUID,
    ):
        raise NotImplementedError

    @abstractmethod
    async def get(self, id: UUID) -> AgentDBE:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        id: UUID,
        values_to_update: Dict[str, Any],
    ) -> AgentDBE:
        raise NotImplementedError

    @abstractmethod
    async def query(
        self,
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[AgentDBE]:
        raise NotImplementedError
