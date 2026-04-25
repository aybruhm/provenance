from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class UserDBE(IDMixin, TimestampMixin):
    __tablename__ = "users"

    username = Column(String)
    password = Column(String)

    api_keys = relationship("ApiKeyDBE", back_populates="user")
    
