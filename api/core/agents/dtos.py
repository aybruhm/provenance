from uuid import UUID

from pydantic import BaseModel


class CreateAgentDTO(BaseModel):
    tenant_id: UUID
    name: str


class UpdateAgentDTO(BaseModel):
    name: str | None = None


class AgentDTO(CreateAgentDTO):
    id: str
    created_at: str
    updated_at: str
