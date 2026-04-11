from sqlalchemy import Boolean, Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class TenantPolicyDBE(IDMixin, TimestampMixin):
    __tablename__ = "tenant_policies"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "policy_id",
            name="uq_tenant_policy",
        ),
    )

    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id"),
        nullable=False,
    )
    policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("policies.id"),
        nullable=False,
    )
    active = Column(Boolean, default=True)
    applied_at = Column(DateTime, server_default=func.now())
    revoked_at = Column(DateTime, nullable=True)

    tenant = relationship("TenantDBE", backref="tenant_policies")
    policy = relationship("PolicyDBE", backref="tenant_policies")
