from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from uuid_utils import uuid7

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class AgentDBE(IDMixin, TimestampMixin):
    __tablename__ = "agents"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "tenant_id",
            name="uq_agents_name_tenant_id",
        ),
    )

    name = Column(String, nullable=False)
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        default=uuid7,
    )
