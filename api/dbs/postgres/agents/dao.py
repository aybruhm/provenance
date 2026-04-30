from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from core.agents.interfaces import AgentDAOInterface
from dbs.postgres.agents.dbes import AgentDBE
from dbs.postgres.engine import get_db_session


class AgentDAO(AgentDAOInterface):
    async def create(
        self,
        name: str,
        tenant_id: UUID,
    ) -> AgentDBE:
        async with get_db_session() as session:
            agent_dbe = AgentDBE(name=name, tenant_id=tenant_id)
            session.add(agent_dbe)
            await session.commit()
            return agent_dbe

    async def get(self, id: UUID) -> AgentDBE | None:
        async with get_db_session() as session:
            stmt = select(AgentDBE).where(AgentDBE.id == id)
            result = await session.execute(stmt)
            agent_dbe = result.scalar_one_or_none()
            if not agent_dbe:
                return None
            return agent_dbe

    async def get_by_name(self, name: str) -> AgentDBE | None:
        async with get_db_session() as session:
            stmt = select(AgentDBE).where(AgentDBE.name == name)
            result = await session.execute(stmt)
            agent_dbe = result.scalar_one_or_none()
            if not agent_dbe:
                return None
            return agent_dbe

    async def update(
        self,
        id: UUID,
        values_to_update: Dict[str, Any],
    ) -> AgentDBE | None:
        try:
            async with get_db_session() as session:
                stmt = (
                    update(AgentDBE)
                    .where(AgentDBE.id == id)
                    .values(**values_to_update)
                    .returning(AgentDBE)
                )
                result = await session.execute(stmt)
                await session.commit()
                agent_dbe = result.scalar_one_or_none()
                if not agent_dbe:
                    return None
                return agent_dbe
        except IntegrityError:
            raise ValueError("Agent with this name already exists")

    async def query(
        self,
        filters: list,
        offset: int,
        limit: int,
    ) -> list[AgentDBE]:
        async with get_db_session() as session:
            stmt = select(AgentDBE).where(*filters).offset(offset).limit(limit)
            result = await session.execute(stmt)
            agent_dbes = result.scalars().all()
            return list(agent_dbes)
