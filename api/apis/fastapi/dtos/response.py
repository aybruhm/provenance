from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from core.agents.dtos import AgentDTO
from core.audit_events.dtos import AuditEventDTO
from core.audit_events.types import ChainValidationResult
from core.escalations.dtos import EscalationDecisionDTO, EscalationDTO
from core.policy.dtos import PolicyDTO
from core.reports.types import GDPRReport, PCIDSSReport, SOC2Report
from core.tenants.dtos import TenantDTO

# ------- Tenants -------


class TenantResponseDTO(BaseModel):
    tenant: TenantDTO


class TenantListResponseDTO(BaseModel):
    tenants: list[TenantDTO]


# ------- Agents -------


class AgentResponseDTO(BaseModel):
    agent: AgentDTO


class AgentListResponseDTO(BaseModel):
    agents: list[AgentDTO]


# ------- Policies -------


class TenantPolicyResponseDTO(BaseModel):
    tenant_policy_id: UUID
    policy: PolicyDTO


class PolicyResponseDTO(BaseModel):
    policy: PolicyDTO


class PolicyListResponseDTO(BaseModel):
    policies: list[PolicyDTO]


# ------- Audits -------


class AuditEventResponseDTO(BaseModel):
    events: list[AuditEventDTO]


class AuditEventIntegrityResponseDTO(BaseModel):
    integrity: ChainValidationResult


# ------- Reports --------


class ReportResponseDTO(BaseModel):
    report: SOC2Report | GDPRReport | PCIDSSReport


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
    event_id: str | None = None
    decision: Decision
    reason: str
    escalation_id: str | None = None
    actor_human_id: str | None = None


# -------- Auth ------------------


class UserResponse(BaseModel):
    id: UUID
    username: str
    created_at: datetime


class JWTTokensDTO(BaseModel):
    access_token: str
    refresh_token: str


class CredentialsDTO(JWTTokensDTO):
    pass


class UserWithCredentialsResponse(BaseModel):
    user: UserResponse
    credentials: CredentialsDTO
