from uuid import UUID

from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement, NamedColumn

from dbs.postgres.audit_events.dbes import AuditEventDBE
from dbs.postgres.audit_events.interfaces import AuditEventDAOInterface
from dbs.postgres.engine import get_db_session


class AuditEventDAO(AuditEventDAOInterface):
    async def create(self, dbe: AuditEventDBE) -> AuditEventDBE:
        async with get_db_session() as session:
            session.add(dbe)
            await session.commit()
            return dbe

    async def get(self, id: UUID) -> AuditEventDBE | None:
        async with get_db_session() as session:
            stmt = select(AuditEventDBE).where(AuditEventDBE.id == id)
            result = await session.execute(stmt)
            audit_event_dbe = result.scalar_one_or_none()
            if not audit_event_dbe:
                return None
            return audit_event_dbe

    async def get_prev_hash(self, tenant_id: UUID) -> AuditEventDBE | None:
        async with get_db_session() as session:
            stmt = (
                select(AuditEventDBE)
                .where(AuditEventDBE.tenant_id == tenant_id)
                .order_by(AuditEventDBE.timestamp.desc())
                .limit(1)
            )
            result = await session.execute(stmt)
            last_event_dbe = result.scalar_one_or_none()
            if not last_event_dbe:
                return None
            return last_event_dbe

    async def query(
        self,
        columns: list[NamedColumn],
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[AuditEventDBE]:
        async with get_db_session() as session:
            stmt = (
                select(AuditEventDBE)
                .with_only_columns(*columns)
                .where(*filters)
                .order_by(AuditEventDBE.timestamp.desc())
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            audit_events_dbes = result.scalars().all()
            return list(audit_events_dbes)
