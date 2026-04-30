from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.sql.elements import ColumnElement, NamedColumn

from core.escalations.interfaces import EscalationDAOInterface
from dbs.postgres.engine import get_db_session
from dbs.postgres.escalations.dbes import EscalationDBE


class EscalationDAO(EscalationDAOInterface):
    async def create(
        self,
        dbe: EscalationDBE,
    ) -> EscalationDBE:
        async with get_db_session() as session:
            session.add(dbe)
            await session.commit()
            return dbe

    async def get(self, id: UUID) -> EscalationDBE | None:
        async with get_db_session() as session:
            stmt = select(EscalationDBE).where(EscalationDBE.id == id)
            result = await session.execute(stmt)
            escalation_dbe = result.scalar_one_or_none()
            if not escalation_dbe:
                return None
            return escalation_dbe

    async def update(
        self,
        id: UUID,
        values_to_update: Dict[str, Any],
    ) -> EscalationDBE | None:
        async with get_db_session() as session:
            stmt = (
                update(EscalationDBE)
                .where(EscalationDBE.id == id)
                .values(**values_to_update)
                .returning(EscalationDBE)
            )
            result = await session.execute(stmt)
            await session.commit()
            escalation_dbe = result.scalar_one_or_none()
            if not escalation_dbe:
                return None
            return escalation_dbe

    async def query(
        self,
        columns: list[NamedColumn],
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[EscalationDBE]:
        async with get_db_session() as session:
            stmt = (
                select(EscalationDBE)
                .with_only_columns(*columns)
                .where(*filters)
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            escalations_dbes = result.scalars().all()
            return list(escalations_dbes)
