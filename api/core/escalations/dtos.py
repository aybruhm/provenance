from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class CreateEscalationDTO(BaseModel):
    tenant_id: UUID
    agent_id: UUID
    action: str
    parameters_hash: str
    status: str = Field(default="PENDING")
    approver_id: str | None = None
    reason: str | None = None
    decided_at: str | None = None


class EscalationDTO(CreateEscalationDTO):
    id: str
    created_at: str
    updated_at: str

    @field_serializer(
        "tenant_id",
        "agent_id",
        when_used="always",
    )
    def serialize_uuid(self, v: UUID) -> str:
        return str(v)


class UpdateEscalationDTO(BaseModel):
    status: str | None = None
    approver_id: str | None = None
    reason: str | None = None
    decided_at: str | None = None


class EscalationDecisionDTO(BaseModel):
    escalation_id: str
    decision: Literal["APPROVE", "REJECT"]
    approver_id: str
    reason: str | None = None
