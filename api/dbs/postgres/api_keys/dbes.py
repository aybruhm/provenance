from sqlalchemy import UUID, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class APIKeyDBE(IDMixin, TimestampMixin):
    __tablename__ = "api_keys"

    prefix = Column(String, unique=True, index=True)
    key_hash = Column(String)
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            name="api_keys_created_by_fkey",
        ),
    )
    scope = Column(
        UUID(as_uuid=True),
        ForeignKey(
            "tenant_policies.id",
            ondelete="CASCADE",
            name="api_keys_scope_fkey",
        ),
    )

    user = relationship("UserDBE", back_populates="api_keys")
    tenant_policy = relationship(
        "TenantPolicyDBE",
        back_populates="api_keys",
    )
