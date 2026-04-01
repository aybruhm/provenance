from uuid import UUID

from pydantic import BaseModel, Field


class CreateEscalationDTO(BaseModel):
    event_id: UUID
    tenant_id: UUID
    agent_id: UUID
    action: str
    parameters_hash: str
    status: str = Field(default="PENDING")
    approver_id: str | None = None
    reason: str | None = None
    decided_at: str | None = None


class EscalationDTO(CreateEscalationDTO):
    id: UUID
    created_at: str
    updated_at: str


class UpdateEscalationDTO(BaseModel):
    status: str | None = None
    approver_id: str | None = None
    reason: str | None = None
    decided_at: str | None = None