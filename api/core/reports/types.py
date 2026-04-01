from typing import Dict

from pydantic import BaseModel

from core.audit_events.dtos import AuditEventDTO
from core.audit_events.types import ChainViolation
from core.escalations.dtos import EscalationDTO


class ReportPeriod(BaseModel):
    start: str | None = None
    end: str | None


class ChainIntegrity(BaseModel):
    valid: bool
    events_checked: int
    violations: list[ChainViolation]


class SOC2ReportSummary(BaseModel):
    total_agent_actions: int
    allowed: int
    blocked: int
    escalated: int
    block_rate_pct: float
    escalation_rate_pct: float
    human_approvals: int
    human_rejections: int


class AgentActions(BaseModel):
    allowed: int
    blocked: int
    escalated: int
    actions: list[str]


class SOC2Report(BaseModel):
    framework: str
    control: str
    tenant_id: str
    report_generated_at: str
    period: ReportPeriod
    audit_chain_integrity: ChainIntegrity
    summary: SOC2ReportSummary
    by_agent: Dict[str, AgentActions]
    escalation_log: list[EscalationDTO]
    events: list[AuditEventDTO]
    attestation: str


class GDPRReportSummary(BaseModel):
    total_data_access_events: int
    agents_with_data_access: list[str]
    distinct_data_actions: list[str]


class GDPRReport(BaseModel):
    framework: str
    record_type: str
    tenant_id: str
    report_generated_at: str
    summary: GDPRReportSummary
    data_access_events: list[AuditEventDTO]
    lawful_basis_note: str


class PCIDSSReportSummary(BaseModel):
    total_payment_actions: int
    allowed: int
    blocked: int
    escalated: int
    human_approved: int
    block_rate_pct: float


class PCIDSSReport(BaseModel):
    framework: str
    control: str
    tenant_id: str
    report_generated_at: str
    summary: PCIDSSReportSummary
    chain_of_custody: list[AuditEventDTO]
    human_approval_events: list[AuditEventDTO]
    attestation: str
