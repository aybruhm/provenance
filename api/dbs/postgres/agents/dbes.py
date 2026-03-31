from sqlalchemy import Column, ForeignKey, String

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class AgentDBE(IDMixin, TimestampMixin):
    __tablename__ = "agents"

    name = Column(String, nullable=False)
    tenant_id = Column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
