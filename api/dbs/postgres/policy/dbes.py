from sqlalchemy import Column, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_json import mutable_json_type

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class PolicyDBE(IDMixin, TimestampMixin):
    __tablename__ = "policies"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "version",
            name="uq_policy_name_version",
        ),
    )

    name = Column(String, nullable=False)
    version = Column(String, nullable=False)
    description = Column(String, nullable=False)
    rules = Column(
        mutable_json_type(JSONB, nested=True),
        default=lambda: {},
        server_default="{}",
        nullable=False,
    )
