from sqlalchemy import Column, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class TenantDBE(IDMixin, TimestampMixin):
    __tablename__ = "tenants"
    __table_args__ = (
        Index(
            "ix_tenants_user_id",
            "user_id",
        ),
        UniqueConstraint(
            "name",
            "user_id",
            name="uq_tenants_name_user_id",
        ),
    )

    name = Column(String, nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
