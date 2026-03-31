from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from uuid_utils import uuid7

from dbs.postgres.shared.dbas import IDMixin, TimestampMixin


class EscalationDBE(IDMixin, TimestampMixin):
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("audit_events.id", ondelete="CASCADE"),
        nullable=True,
        default=uuid7,
    )
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        default=uuid7,
    )
    agent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        default=uuid7,
    )
    action = Column(String, nullable=False)
    parameters_hash = Column(
        String, nullable=False
    )  # SHA-256 of canonical JSON parameters
    status = Column(String, nullable=False, default="PENDING")
    approver_id = Column(String, nullable=True)  # approver identity
    decided_at = Column(String, nullable=True)  # ISO 8601 format
    reason = Column(String, nullable=True)
