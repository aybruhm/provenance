from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from core.agents.dtos import CreateAgentDTO, UpdateAgentDTO
from core.api_keys.dtos import CreateAPIKeyDTO, UpdateAPIKeyScopeDTO
from core.audit_events.dtos import CreateAuditEventDTO
from core.escalations.dtos import CreateEscalationDTO
from core.policy.dtos import CreatePolicyDTO, UpdatePolicyDTO
from core.tenants.dtos import CreateTenantDTO, UpdateTenantDTO
from core.users.dtos import LoginUserDTO, RegisterUserDTO

# ----- Tenants -----


class TenantCreateRequestDTO(CreateTenantDTO):
    pass


class TenantUpdateRequestDTO(UpdateTenantDTO):
    pass


# ------ Agents ----------


class AgentCreateRequestDTO(CreateAgentDTO):
    pass


class AgentUpdateRequestDTO(UpdateAgentDTO):
    pass


# ------ Policies ----------


class PolicyCreateRequestDTO(CreatePolicyDTO):
    pass


class PolicyUpdateRequestDTO(UpdatePolicyDTO):
    pass


class AssignPolicyToTenantRequestDTO(BaseModel):
    tenant_id: UUID


class DeactivateTenantPolicyRequestDTO(BaseModel):
    active: bool


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


# ------ API Keys ----------


class APIKeyCreateRequestDTO(CreateAPIKeyDTO):
    pass


class APIKeyUpdateScopeRequestDTO(UpdateAPIKeyScopeDTO):
    pass


# ------ Auth -----


class RegisterUserRequestDTO(RegisterUserDTO):
    pass


class LoginUserRequestDTO(LoginUserDTO):
    pass


class RefreshTokensRequestDTO(BaseModel):
    refresh_token: str
