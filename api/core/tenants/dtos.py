from pydantic import BaseModel


class CreateTenantDTO(BaseModel):
    name: str


class UpdateTenantDTO(BaseModel):
    name: str | None = None


class TenantDTO(CreateTenantDTO):
    id: str
    created_at: str
    updated_at: str
