from uuid import UUID

from pydantic import BaseModel


class CreateAPIKeyDTO(BaseModel):
    user_id: UUID
    scope_id: UUID


class UpdateAPIKeyScopeDTO(BaseModel):
    scope_id: UUID


class CreatedBy(BaseModel):
    id: str
    username: str


class APIKeyDTO(BaseModel):
    id: str
    prefix: str
    key_hash: str
    scope: str
    created_by: CreatedBy
    created_at: str
    updated_at: str
