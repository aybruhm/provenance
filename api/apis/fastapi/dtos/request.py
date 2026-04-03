from typing import Literal

from pydantic import BaseModel

from core.audit_events.dtos import CreateAuditEventDTO
from core.escalations.dtos import CreateEscalationDTO

# ----- Execution Gateway -----


class ExecuteRequestDTO(CreateAuditEventDTO):
    idempotency_key: str | None = None


# ------ Escalation ----------


class EscalationDecisionRequestDTO(BaseModel):
    decision: Literal["APPROVE", "REJECT"]
    approver_id: str
    reason: str | None = None


class EscalationCreateRequestDTO(CreateEscalationDTO):
    pass
