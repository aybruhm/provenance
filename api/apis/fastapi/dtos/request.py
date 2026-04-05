from typing import Literal

from pydantic import BaseModel

from core.audit_events.dtos import CreateAuditEventDTO
from core.escalations.dtos import CreateEscalationDTO
from core.tenants.dtos import CreateTenantDTO, UpdateTenantDTO
from core.users.dtos import LoginUserDTO, RegisterUserDTO

# ----- Tenants -----


class TenantCreateRequestDTO(CreateTenantDTO):
    pass


class TenantUpdateRequestDTO(UpdateTenantDTO):
    pass


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


# ------ Auth -----


class RegisterUserRequestDTO(RegisterUserDTO):
    pass


class LoginUserRequestDTO(LoginUserDTO):
    pass


class RefreshTokensRequestDTO(BaseModel):
    refresh_token: str
