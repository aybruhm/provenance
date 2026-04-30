from typing import Any, Dict
from uuid import UUID

from sqlalchemy import delete, select, update

from core.policy.interfaces import PolicyDAOInterface
from dbs.postgres.engine import get_db_session
from dbs.postgres.policy.dbes import PolicyDBE


class PolicyDAO(PolicyDAOInterface):
    async def create_policy(self, policy_dbe: PolicyDBE) -> PolicyDBE:
        async with get_db_session() as session:
            session.add(policy_dbe)
            await session.commit()
            return policy_dbe

    async def get_policy(self, policy_id: UUID) -> PolicyDBE | None:
        async with get_db_session() as session:
            result = await session.execute(
                select(PolicyDBE).where(PolicyDBE.id == policy_id)
            )
            policy_dbe = result.scalar_one_or_none()
            return policy_dbe

    async def get_policy_by_name(self, name: str) -> PolicyDBE | None:
        async with get_db_session() as session:
            result = await session.execute(
                select(PolicyDBE).where(PolicyDBE.name == name)
            )
            policy_dbe = result.scalar_one_or_none()
            return policy_dbe

    async def update_policy(
        self,
        policy_id: UUID,
        values_to_update: Dict[str, Any],
    ) -> PolicyDBE | None:
        async with get_db_session() as session:
            stmt = (
                update(PolicyDBE)
                .where(PolicyDBE.id == policy_id)
                .values(values_to_update)
                .returning(PolicyDBE)
            )
            result = await session.execute(stmt)
            await session.commit()
            updated_policy_dbe = result.scalar_one_or_none()
            return updated_policy_dbe

    async def delete_policy(self, policy_id: UUID) -> None:
        async with get_db_session() as session:
            stmt = delete(PolicyDBE).where(PolicyDBE.id == policy_id)
            await session.execute(stmt)
            await session.commit()
