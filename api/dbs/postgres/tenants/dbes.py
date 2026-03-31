from sqlalchemy import Column, String

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class TenantDBE(IDMixin, TimestampMixin):
    __tablename__ = "tenants"

    name = Column(String, nullable=False)
    policy_id = Column(String, nullable=False)
