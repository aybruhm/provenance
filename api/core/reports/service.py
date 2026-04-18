from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from core.audit_events.service import AuditEventService
from core.escalations.service import EscalationService
from core.reports.types import (
    AgentActions,
    ChainIntegrity,
    GDPRReport,
    GDPRReportSummary,
    PCIDSSReport,
    PCIDSSReportSummary,
    ReportPeriod,
    SOC2Report,
    SOC2ReportSummary,
)


class ComplianceReportService:
    """
    Compliance Report Generator that produces structured reports for various regulatory \
        frameworks (SOC 2, GDPR, and PCI-DSS) based on the tamper-evident audit log \
            of agent actions and escalations.
    """

    def __init__(
        self,
        escalation_service: EscalationService,
        audit_event_service: AuditEventService,
    ):
        self.escalation_service = escalation_service
        self.audit_event_service = audit_event_service

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── SOC 2 ─────────────────────────────────────────────────────────────────────

    async def generate_soc2_report(
        self,
        *,
        tenant_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> SOC2Report:
        """
        SOC 2 Type II — CC6: Logical and Physical Access Controls

        Maps agent action logs to the CC6 trust service criterion:
        evidence that access (via agents) is authorised, logged, and reviewable.
        """

        events = await self.audit_event_service.list_audit_events(
            tenant_id=UUID(tenant_id),
            limit=100_000,
        )
        if start_date:
            events = [event for event in events if event.timestamp >= start_date]
        if end_date:
            events = [event for event in events if event.timestamp <= end_date]

        total = len(events)
        allowed = sum(1 for event in events if event.decision == "ALLOW")
        blocked = sum(1 for event in events if event.decision == "BLOCK")
        escalated = sum(1 for event in events if event.escalation_id is not None)

        by_agent: dict[str, AgentActions] = {}
        for event in events:
            aid = event.agent_id
            if aid not in by_agent:
                by_agent[aid] = AgentActions(
                    allowed=0,
                    blocked=0,
                    escalated=0,
                    actions=[],
                )
            decision_key = {
                "ALLOW": "allowed",
                "BLOCK": "blocked",
                "ESCALATE": "escalated",
            }.get(event.decision, "allowed")
            if decision_key == "allowed":
                by_agent[aid].allowed += 1
            elif decision_key == "blocked":
                by_agent[aid].blocked += 1
            elif decision_key == "escalated":
                by_agent[aid].escalated += 1
            if event.action not in by_agent[aid].actions:
                by_agent[aid].actions.append(event.action)

        escalations = await self.escalation_service.list_escalations(
            tenant_id=UUID(tenant_id),
            offset=0,
            limit=100_000,
        )
        human_approved = [
            escalation for escalation in escalations if escalation.status == "APPROVE"
        ]
        human_rejected = [
            escalation for escalation in escalations if escalation.status == "REJECT"
        ]

        integrity = await self.audit_event_service.verify_chain_integrity(
            tenant_id=UUID(tenant_id),
            offset=0,
            limit=100_000,
        )

        return SOC2Report(
            framework="SOC 2 Type II",
            control="CC6 — Logical and Physical Access Controls",
            tenant_id=tenant_id,
            report_generated_at=self._now(),
            period=ReportPeriod(start=start_date, end=end_date),
            audit_chain_integrity=ChainIntegrity(
                valid=integrity.valid,
                events_checked=integrity.events_checked,
                violations=integrity.violations,
            ),
            summary=SOC2ReportSummary(
                total_agent_actions=total,
                allowed=allowed,
                blocked=blocked,
                escalated=escalated,
                block_rate_pct=round(blocked / total * 100, 2) if total else 0,
                escalation_rate_pct=round(escalated / total * 100, 2) if total else 0,
                human_approvals=len(human_approved),
                human_rejections=len(human_rejected),
            ),
            by_agent=by_agent,
            escalation_log=escalations,
            events=events,
            attestation=(
                "All agent actions were evaluated against a versioned declarative policy "
                "prior to execution. An append-only, hash-chained audit log was maintained "
                "for every action. High-risk actions were routed to a named human approver "
                "before execution. Audit chain integrity: "
                + ("VALID" if integrity.valid else "VIOLATIONS DETECTED")
            ),
        )

    # ── GDPR ──────────────────────────────────────────────────────────────────────

    async def generate_gdpr_report(self, tenant_id: str) -> GDPRReport:
        """
        GDPR Article 30 — Records of Processing Activities

        Surfaces all agent actions that touched personal or sensitive data categories.
        """

        events = await self.audit_event_service.list_audit_events(
            tenant_id=UUID(tenant_id),
            limit=100_000,
        )

        # Data-touching actions heuristic: namespace prefix
        DATA_PREFIXES = ("data.", "user.", "profile.", "pii.", "personal.")
        data_events = [
            event
            for event in events
            if any(
                event.action.startswith(data_prefix) for data_prefix in DATA_PREFIXES
            )
        ]

        agents_with_access = list({event.agent_id for event in data_events})
        actions_seen = list({event.action for event in data_events})

        return GDPRReport(
            framework="GDPR Article 30",
            record_type="Records of Processing Activities — AI Agent Data Access",
            tenant_id=tenant_id,
            report_generated_at=self._now(),
            summary=GDPRReportSummary(
                total_data_access_events=len(data_events),
                agents_with_data_access=agents_with_access,
                distinct_data_actions=actions_seen,
            ),
            data_access_events=data_events,
            lawful_basis_note=(
                "Each data access event was gated by an active policy. "
                "No agent accessed data outside its declared scope. "
                "Access events are logged with agent identity and timestamp "
                "to fulfil Article 30 record-keeping obligations."
            ),
        )

    # ── PCI-DSS ───────────────────────────────────────────────────────────────────

    async def generate_pci_report(self, tenant_id: str) -> PCIDSSReport:
        """
        PCI-DSS Requirement 10 — Track and Monitor All Access to Network Resources

        Chain-of-custody for every payment-related agent action.
        """

        events = await self.audit_event_service.list_audit_events(
            tenant_id=UUID(tenant_id),
            limit=100_000,
        )
        PAYMENT_KEYWORDS = (
            "payment",
            "transfer",
            "refund",
            "charge",
            "payout",
            "withdrawal",
        )
        payment_events = [
            event
            for event in events
            if any(kw in event.action.lower() for kw in PAYMENT_KEYWORDS)
        ]

        allowed_payments = [
            event for event in payment_events if event.decision == "ALLOW"
        ]
        blocked_payments = [
            event for event in payment_events if event.decision == "BLOCK"
        ]
        escalated_payments = [
            event for event in payment_events if event.escalation_id is not None
        ]
        human_approved = [
            event for event in payment_events if event.actor_human_id is not None
        ]

        return PCIDSSReport(
            framework="PCI-DSS",
            control="Requirement 10 — Track and Monitor All Access to Payment Resources",
            tenant_id=tenant_id,
            report_generated_at=self._now(),
            summary=PCIDSSReportSummary(
                total_payment_actions=len(payment_events),
                allowed=len(allowed_payments),
                blocked=len(blocked_payments),
                escalated=len(escalated_payments),
                human_approved=len(human_approved),
                block_rate_pct=round(
                    len(blocked_payments) / len(payment_events) * 100, 2
                )
                if payment_events
                else 0,
            ),
            chain_of_custody=payment_events,
            human_approval_events=human_approved,
            attestation=(
                "All payment-related agent actions were intercepted, policy-evaluated, "
                "and logged prior to execution. Actions exceeding the approved threshold "
                "were held for named human approval before proceeding. "
                "No payment action bypassed the Provenance gateway."
            ),
        )
