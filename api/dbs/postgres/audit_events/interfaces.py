from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.sql.elements import ColumnElement

from dbs.postgres.audit_events.dbes import AuditEventDBE


class AuditEventDAOInterface(ABC):
    @abstractmethod
    async def create(self, dbe: AuditEventDBE):
        raise NotImplementedError

    @abstractmethod
    async def get(self, id: UUID) -> AuditEventDBE:
        raise NotImplementedError

    @abstractmethod
    async def query(
        self,
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[AuditEventDBE]:
        raise NotImplementedError
