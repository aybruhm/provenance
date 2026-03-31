from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from sqlalchemy.sql.elements import ColumnElement

from dbs.postgres.escalations.dbes import EscalationDBE


class EscalationDAOInterface(ABC):
    @abstractmethod
    async def create(
        self,
        dbe: EscalationDBE,
    ) -> EscalationDBE:
        raise NotImplementedError

    @abstractmethod
    async def get(self, id: UUID) -> EscalationDBE | None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        id: UUID,
        values_to_update: Dict[str, Any],
    ) -> EscalationDBE:
        raise NotImplementedError

    @abstractmethod
    async def query(
        self,
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[EscalationDBE]:
        raise NotImplementedError
