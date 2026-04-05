from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import ColumnElement

from dbs.postgres.engine import get_db_session
from dbs.postgres.tenants.dbes import TenantDBE
from dbs.postgres.tenants.interfaces import TenantDAOInterface


class TenantDAO(TenantDAOInterface):
    async def create(
        self,
        name: str,
        policy_id: str,
        user_id: UUID,
    ) -> TenantDBE:
        async with get_db_session() as session:
            tenant_dbe = TenantDBE(
                name=name,
                policy_id=policy_id,
                user_id=user_id,
            )
            session.add(tenant_dbe)
            await session.commit()
            return tenant_dbe

    async def get(self, id: UUID, user_id: UUID) -> TenantDBE | None:
        async with get_db_session() as session:
            stmt = select(TenantDBE).where(
                TenantDBE.id == id,
                TenantDBE.user_id == user_id,
            )
            tenant_dbe = await session.execute(stmt)
            tenant_dbe = tenant_dbe.scalar_one_or_none()
            if not tenant_dbe:
                return None
            return tenant_dbe

    async def get_by_name(self, name: str, user_id: UUID) -> TenantDBE | None:
        async with get_db_session() as session:
            stmt = select(TenantDBE).where(
                TenantDBE.name == name,
                TenantDBE.user_id == user_id,
            )
            tenant_dbe = await session.execute(stmt)
            tenant_dbe = tenant_dbe.scalar_one_or_none()
            if not tenant_dbe:
                return None
            return tenant_dbe

    async def update(
        self,
        id: UUID,
        user_id: UUID,
        values_to_update: Dict[str, Any],
    ) -> TenantDBE | None:
        try:
            async with get_db_session() as session:
                stmt = (
                    update(TenantDBE)
                    .where(
                        TenantDBE.id == id,
                        TenantDBE.user_id == user_id,
                    )
                    .values(**values_to_update)
                    .returning(TenantDBE)
                )
                result = await session.execute(stmt)
                await session.commit()
                tenant_dbe = result.scalar_one_or_none()
                if not tenant_dbe:
                    return None
                return tenant_dbe
        except IntegrityError:
            raise ValueError("Tenant with the same name already exists")

    async def query(
        self,
        user_id: UUID,
        filters: list[ColumnElement],
        offset: int,
        limit: int,
    ) -> list[TenantDBE]:
        async with get_db_session() as session:
            stmt = (
                select(TenantDBE)
                .where(
                    TenantDBE.user_id == user_id,
                    *filters,
                )
                .offset(offset)
                .limit(limit)
            )
            result = await session.execute(stmt)
            tenants_dbes = result.scalars().all()
            return list(tenants_dbes)
