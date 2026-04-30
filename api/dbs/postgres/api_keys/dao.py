from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.elements import ColumnElement

from core.api_keys.interfaces import APIKeyDAOInterface
from dbs.postgres.api_keys.dbes import APIKeyDBE
from dbs.postgres.engine import get_db_session
from dbs.postgres.users.dbes import UserDBE


class APIKeyDAO(APIKeyDAOInterface):
    async def create(self, api_key: APIKeyDBE) -> APIKeyDBE:
        async with get_db_session() as session:
            session.add(api_key)
            await session.commit()
            await session.refresh(
                api_key,
                attribute_names=["user"],
            )
            return api_key

    async def query(
        self,
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[APIKeyDBE]:
        async with get_db_session() as session:
            result = await session.execute(
                select(APIKeyDBE)
                .options(
                    joinedload(APIKeyDBE.user).load_only(
                        UserDBE.id,  # type: ignore
                        UserDBE.username,  # type: ignore
                    )
                )
                .filter(*filters)
                .offset(offset)
                .limit(limit)
            )
            api_keys_dbes = result.scalars().all()
            return list(api_keys_dbes)

    async def list(
        self,
        tenant_id: UUID,
        offset: int,
        limit: int,
    ) -> list[APIKeyDBE]:
        async with get_db_session() as session:
            result = await session.execute(
                select(APIKeyDBE)
                .options(
                    joinedload(APIKeyDBE.user).load_only(
                        UserDBE.id,  # type: ignore
                        UserDBE.username,  # type: ignore
                    )
                )
                .filter_by(tenant_id=tenant_id)
                .offset(offset)
                .limit(limit)
            )
            api_keys_dbes = result.scalars().all()
            return list(api_keys_dbes)

    async def get_by_prefix(self, prefix: str) -> APIKeyDBE | None:
        async with get_db_session() as session:
            stmt = (
                select(APIKeyDBE)
                .options(
                    joinedload(APIKeyDBE.user).load_only(
                        UserDBE.id,  # type: ignore
                        UserDBE.username,  # type: ignore
                    )
                )
                .filter_by(prefix=prefix)
            )
            result = await session.execute(stmt)
            api_key_dbe = result.scalar_one_or_none()
            return api_key_dbe

    async def update_scope(self, id: UUID, scope: UUID) -> APIKeyDBE | None:
        async with get_db_session() as session:
            stmt = (
                update(APIKeyDBE)
                .where(APIKeyDBE.id == id)
                .values(scope=scope)
                .returning(APIKeyDBE)
            )
            result = await session.execute(stmt)
            await session.commit()
            api_key_dbe = result.scalar_one_or_none()
            return api_key_dbe

    async def delete(self, id: UUID) -> None:
        async with get_db_session() as session:
            stmt = delete(APIKeyDBE).where(APIKeyDBE.id == id)
            await session.execute(stmt)
            await session.commit()
