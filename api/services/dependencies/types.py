from uuid import UUID

from pydantic import BaseModel


class CurrentUserContext(BaseModel):
    id: UUID
    username: str
    token: str


class CurrentScopeContext(BaseModel):
    id: UUID
    username: str
    scope: str
