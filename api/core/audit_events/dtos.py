from typing import Any, Dict

from pydantic import BaseModel


class CreateAuditEventDTO(BaseModel):
    session_id: str
    agent_id: str
    tenant_id: str
    action: str
    # NOTE: tenant_policy_id is optional
    # On sdk requests, it'll automatically be set.
    # On api requests, it'll be explicitly set by the caller.
    tenant_policy_id: str | None = None
    parameters: Dict[str, Any] | None = None
    decision: str
    escalation_id: str | None = None
    actor_human_id: str | None = None


class AuditEventDTO(CreateAuditEventDTO):
    id: str
    payload_hash: str
    prev_hash: str
    timestamp: str
