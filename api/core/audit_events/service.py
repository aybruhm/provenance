from datetime import datetime
from uuid import UUID

from core.audit_events import utils
from core.audit_events.dtos import AuditEventDTO, CreateAuditEventDTO
from core.audit_events.types import ChainValidationResult, ChainViolation
from dbs.postgres.audit_events.dbes import AuditEventDBE
from dbs.postgres.audit_events.interfaces import AuditEventDAOInterface
from dbs.postgres.escalations.interfaces import EscalationDAOInterface


class AuditEventService:
    def __init__(
        self,
        audit_event_dao: AuditEventDAOInterface,
        escalation_dao: EscalationDAOInterface,
    ):
        self.audit_event_dao = audit_event_dao
        self.escalation_dao = escalation_dao

    def _map_dbe_to_dto(self, dbe: AuditEventDBE) -> AuditEventDTO:
        return AuditEventDTO(
            id=str(dbe.id),  # type: ignore
            session_id=dbe.session_id,  # type: ignore
            agent_id=str(dbe.agent_id),  # type: ignore
            tenant_id=str(dbe.tenant_id),  # type: ignore
            tenant_policy_id=str(dbe.tenant_policy_id),  # type: ignore
            action=dbe.action,  # type: ignore
            payload_hash=dbe.payload_hash,  # type: ignore
            decision=dbe.decision,  # type: ignore
            escalation_id=dbe.escalation_id,  # type: ignore
            actor_human_id=dbe.actor_human_id,  # type: ignore
            prev_hash=dbe.prev_hash,  # type: ignore
            timestamp=dbe.timestamp,  # type: ignore
        )

    def _map_dto_to_dbe(self, dto: CreateAuditEventDTO) -> AuditEventDBE:
        return AuditEventDBE(
            session_id=dto.session_id,
            agent_id=dto.agent_id,
            tenant_policy_id=dto.tenant_policy_id,
            action=dto.action,
            decision=dto.decision,
            escalation_id=dto.escalation_id,
            actor_human_id=dto.actor_human_id,
        )

    def _get_utc_timestamp(self) -> str:
        return datetime.now().isoformat()

    async def create_audit_event(
        self, tenant_id: str, create_data: CreateAuditEventDTO
    ) -> AuditEventDTO:
        audit_event_dbe = self._map_dto_to_dbe(dto=create_data)
        audit_event_dbe.tenant_id = tenant_id  # type: ignore
        if create_data.parameters:
            audit_event_dbe.payload_hash = utils.hash_payload(  # type: ignore
                payload=create_data.parameters
            )
            audit_event_dbe.prev_hash = await self.get_prev_hash(  # type: ignore
                tenant_id=UUID(tenant_id)
            )
            audit_event_dbe.timestamp = self._get_utc_timestamp()  # type: ignore

        audit_event_dbe = await self.audit_event_dao.create(dbe=audit_event_dbe)
        if create_data.escalation_id:
            # Backfill escalation → event link
            await self.escalation_dao.update(
                id=UUID(audit_event_dbe.escalation_id),  # type: ignore
                values_to_update={
                    "event_id": audit_event_dbe.id,
                },
            )

        audit_event_dto = self._map_dbe_to_dto(dbe=audit_event_dbe)
        return audit_event_dto

    async def get_audit_event(self, id: UUID) -> AuditEventDTO | None:
        audit_event_dbe = await self.audit_event_dao.get(id=id)
        if not audit_event_dbe:
            return None
        audit_event_dto = self._map_dbe_to_dto(dbe=audit_event_dbe)
        return audit_event_dto

    async def get_prev_hash(self, tenant_id: UUID) -> str:
        last_event_dbe = await self.audit_event_dao.get_prev_hash(tenant_id=tenant_id)
        if not last_event_dbe:
            return utils.GENESIS_HASH
        return utils.chain_hash(
            event_id=str(last_event_dbe.id),  # type: ignore
            timestamp=str(last_event_dbe.timestamp),  # type: ignore
            payload_hash=last_event_dbe.payload_hash,  # type: ignore
        )

    async def verify_chain_integrity(
        self,
        tenant_id: UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> ChainValidationResult:
        """
        Walk the audit chain for a tenant and verify every prev_hash link.
        Returns a report with any violations found.
        """

        events = await self.list_audit_events(
            tenant_id=tenant_id,
            offset=offset,
            limit=limit,
        )
        violations: list[ChainViolation] = []

        for i, event in enumerate(events):
            if i == 0:
                expected = utils.GENESIS_HASH
            else:
                prev_event = events[i - 1]
                expected = utils.chain_hash(
                    prev_event.id,
                    prev_event.timestamp,
                    prev_event.payload_hash,
                )

            if event.prev_hash != expected:
                violations.append(
                    ChainViolation(
                        position=i,
                        event_id=event.id,
                        expected_prev_hash=expected,
                        actual_prev_hash=event.prev_hash,
                    )
                )

        return ChainValidationResult(
            tenant_id=str(tenant_id),
            valid=len(violations) == 0,
            events_checked=len(events),
            violations=violations,
        )

    async def list_audit_events(
        self,
        tenant_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuditEventDTO]:
        return await self.query_audit_events(
            columns=[AuditEventDBE],  # type: ignore
            filters=[AuditEventDBE.tenant_id == tenant_id],
            offset=offset,
            limit=limit,
        )

    async def query_audit_events(
        self,
        columns: list,
        filters: list,
        offset: int,
        limit: int,
    ) -> list[AuditEventDTO]:
        audit_events_dbes = await self.audit_event_dao.query(
            columns=columns,
            filters=filters,
            offset=offset,
            limit=limit,
        )
        audit_events_dtos = [
            self._map_dbe_to_dto(dbe=audit_event_dbe)
            for audit_event_dbe in audit_events_dbes
        ]
        return audit_events_dtos
