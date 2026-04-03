from enum import Enum

from pydantic import BaseModel

from core.audit_events.dtos import AuditEventDTO
from core.audit_events.types import ChainValidationResult
from core.escalations.dtos import EscalationDecisionDTO, EscalationDTO

# ------- Audits -------


class AuditEventResponseDTO(BaseModel):
    events: list[AuditEventDTO]


class AuditEventIntegrityResponseDTO(BaseModel):
    integrity: ChainValidationResult


# ------- Escalations -------


class EscalationResponseDTO(BaseModel):
    escalations: list[EscalationDTO]


class EscalationDecisionResponseDTO(EscalationDecisionDTO):
    pass


# ------- Execution Gateway -------


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class ExecuteResponseDTO(BaseModel):
    event_id: str
    decision: Decision
    reason: str
    escalation_id: str | None = None
    actor_human_id: str | None = None
