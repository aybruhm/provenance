from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from uuid_utils import uuid7

from dbs.postgres.base import Base


class IDMixin(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid7)


class TimestampMixin(Base):
    __abstract__ = True

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class SoftDeleteMixin(Base):
    __abstract__ = True

    deleted_at = Column(DateTime, nullable=True)
