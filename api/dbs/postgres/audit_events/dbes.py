from enum import StrEnum

from sqlalchemy import Column, Enum, ForeignKey, Index, String

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
    agent_id = Column(ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)  # SHA-256 of canonical JSON payload
    decision = Column(Enum(Decision, name="audit_event_decision"), nullable=False)
    escalation_id = Column(String, nullable=True)
    actor_human_id = Column(String, nullable=True)  # approver identity if escalated
    prev_hash = Column(String, nullable=False)  # SHA-256 chain link
    timestamp = Column(String, nullable=False)  # ISO 8601 format
