from sqlalchemy import Column, String

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class UserDBE(IDMixin, TimestampMixin):
    __tablename__ = "users"

    username = Column(String)
    password = Column(String)
