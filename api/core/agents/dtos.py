from uuid import UUID

from pydantic import BaseModel


class CreateAgentDTO(BaseModel):
    tenant_id: UUID
    name: str


class UpdateAgentDTO(BaseModel):
    name: str | None = None


class AgentDTO(CreateAgentDTO):
    id: UUID
    created_at: str
    updated_at: str
