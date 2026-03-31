from sqlalchemy import Column, ForeignKey, String

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class EscalationDBE(IDMixin, TimestampMixin):
    event_id = Column(
        String, ForeignKey("audit_events.id", ondelete="CASCADE"), nullable=True
    )
    tenant_id = Column(
        String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    agent_id = Column(
        String, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    action = Column(String, nullable=False)
    parameters_hash = Column(
        String, nullable=False
    )  # SHA-256 of canonical JSON parameters
    status = Column(String, nullable=False, default="PENDING")
    approver_id = Column(String, nullable=True)  # approver identity
    decided_at = Column(String, nullable=True)  # ISO 8601 format
    reason = Column(String, nullable=True)
