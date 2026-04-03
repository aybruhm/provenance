from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, update

from dbs.postgres.engine import get_db_session
from dbs.postgres.users.dbes import UserDBE
from dbs.postgres.users.interfaces import UserDAOInterface


class UserDAO(UserDAOInterface):
    async def create(self, user_dbe: UserDBE) -> UserDBE:
        async with get_db_session() as session:
            session.add(user_dbe)
            await session.commit()
            await session.refresh(user_dbe)
            return user_dbe

    async def get_by_id(self, user_id: UUID) -> UserDBE | None:
        async with get_db_session() as session:
            stmt = select(UserDBE).where(UserDBE.id == user_id)
            result = await session.execute(stmt)
            user_dbe = result.scalar_one_or_none()
            return user_dbe

    async def get_by_username(self, username: str) -> UserDBE | None:
        async with get_db_session() as session:
            stmt = select(UserDBE).where(UserDBE.username == username)
            result = await session.execute(stmt)
            user_dbe = result.scalar_one_or_none()
            return user_dbe

    async def update(
        self,
        user_id: UUID,
        values_to_update: Dict[str, Any],
    ) -> UserDBE | None:
        async with get_db_session() as session:
            stmt = (
                update(UserDBE)
                .where(UserDBE.id == user_id)
                .values(**values_to_update)
                .returning(UserDBE)
            )
            result = await session.execute(stmt)
            await session.commit()

            user_dbe = result.scalar_one_or_none()
            if not user_dbe:
                return None

            await session.refresh(user_dbe)
            return user_dbe
