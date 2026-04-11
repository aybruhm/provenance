from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import joinedload

from dbs.postgres.engine import get_db_session
from dbs.postgres.tenant_policies.dbes import TenantPolicyDBE
from dbs.postgres.tenant_policies.interfaces import TenantPolicyInterface


class TenantPolicyDAO(TenantPolicyInterface):
    async def create_tenant_policy(
        self, tenant_id: UUID, policy_id: UUID
    ) -> TenantPolicyDBE:
        async with get_db_session() as session:
            tenant_policy_dbe = TenantPolicyDBE(
                tenant_id=tenant_id,
                policy_id=policy_id,
                applied_at=datetime.now(timezone.utc),
            )
            session.add(tenant_policy_dbe)
            await session.commit()
            return tenant_policy_dbe

    async def get_tenant_policy(self, tenant_policy_id: UUID) -> TenantPolicyDBE | None:
        async with get_db_session() as session:
            stmt = (
                select(TenantPolicyDBE)
                .options(
                    joinedload(TenantPolicyDBE.policy),
                )
                .filter_by(id=tenant_policy_id)
            )
            result = await session.execute(stmt)
            tenant_policy_dbe = result.scalar_one_or_none()
            return tenant_policy_dbe

    async def update_tenant_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
        active: bool,
    ) -> TenantPolicyDBE | None:
        async with get_db_session() as session:
            stmt = (
                update(TenantPolicyDBE)
                .filter_by(
                    tenant_id=tenant_id,
                    policy_id=policy_id,
                )
                .values(
                    active=active,
                    revoked_at=datetime.now(timezone.utc) if not active else None,
                )
                .returning(TenantPolicyDBE)
            )
            result = await session.execute(stmt)
            tenant_policy_dbe = result.scalar_one_or_none()
            await session.commit()
            return tenant_policy_dbe

    async def delete_tenant_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> None:
        async with get_db_session() as session:
            stmt = delete(TenantPolicyDBE).filter_by(
                tenant_id=tenant_id,
                policy_id=policy_id,
            )
            await session.execute(stmt)
            await session.commit()
