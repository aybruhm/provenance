from enum import StrEnum

from sqlalchemy import Column, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from uuid_utils import uuid7

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class AuditEventDBE(IDMixin, TimestampMixin):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index(
            "ix_audit_events_session_id_timestamp",
            "session_id",
            "timestamp",
        ),
        Index(
            "ix_audit_events_agent_id_timestamp",
            "agent_id",
            "timestamp",
        ),
        Index(
            "ix_audit_events_tenant_id_timestamp",
            "tenant_id",
            "timestamp",
        ),
    )

    class Decision(StrEnum):
        ALLOW = "ALLOW"
        BLOCK = "BLOCK"
        ESCALATE = "ESCALATE"

    session_id = Column(String, nullable=False)
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        default=uuid7,
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        default=uuid7,
    )
    tenant_policy_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenant_policies.id", ondelete="SET NULL"),
        nullable=False,
    )
    action = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)  # SHA-256 of canonical JSON payload
    decision = Column(Enum(Decision, name="audit_event_decision"), nullable=False)
    escalation_id = Column(String, nullable=True)
    actor_human_id = Column(String, nullable=True)  # approver identity if escalated
    prev_hash = Column(String, nullable=False)  # SHA-256 chain link
    timestamp = Column(String, nullable=False)  # ISO 8601 format
