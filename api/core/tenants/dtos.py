from uuid import UUID

from pydantic import BaseModel


class CreateTenantDTO(BaseModel):
    policy_id: str
    name: str


class UpdateTenantDTO(BaseModel):
    name: str | None = None


class TenantDTO(CreateTenantDTO):
    id: UUID
    created_at: str
    updated_at: str
