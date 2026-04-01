from uuid import UUID

from core.audit_events.dtos import AuditEventDTO, CreateAuditEventDTO
from dbs.postgres.audit_events.dbes import AuditEventDBE
from dbs.postgres.audit_events.interfaces import AuditEventDAOInterface


class AuditEventService:
    def __init__(self, audit_event_dao: AuditEventDAOInterface):
        self.audit_event_dao = audit_event_dao

    def _map_dbe_to_dto(self, dbe: AuditEventDBE) -> AuditEventDTO:
        return AuditEventDTO(
            id=dbe.id,  # type: ignore
            session_id=dbe.session_id,  # type: ignore
            agent_id=dbe.agent_id,  # type: ignore
            tenant_id=dbe.tenant_id,  # type: ignore
            action=dbe.action,  # type: ignore
            payload_hash=dbe.payload_hash,  # type: ignore
            decision=dbe.decision,  # type: ignore
            escalation_id=dbe.escalation_id,  # type: ignore
            actor_human_id=dbe.actor_human_id,  # type: ignore
            prev_hash=dbe.prev_hash,  # type: ignore
            timestamp=dbe.timestamp,  # type: ignore
            event_data=dbe.event_data,  # type: ignore
            created_at=dbe.created_at,  # type: ignore
        )

    def _map_dto_to_dbe(self, dto: CreateAuditEventDTO) -> AuditEventDBE:
        return AuditEventDBE(
            session_id=dto.session_id,
            agent_id=dto.agent_id,
            tenant_id=dto.tenant_id,
            action=dto.action,
            parameters=dto.parameters,
            decision=dto.decision,
            escalation_id=dto.escalation_id,
            actor_human_id=dto.actor_human_id,
        )

    async def create_audit_event(
        self, create_data: CreateAuditEventDTO
    ) -> AuditEventDTO:
        audit_event_dbe = self._map_dto_to_dbe(dto=create_data)
        audit_event_dbe = await self.audit_event_dao.create(dbe=audit_event_dbe)
        audit_event_dto = self._map_dbe_to_dto(dbe=audit_event_dbe)
        return audit_event_dto

    async def get_audit_event(self, id: UUID) -> AuditEventDTO | None:
        audit_event_dbe = await self.audit_event_dao.get(id=id)
        if not audit_event_dbe:
            return None
        audit_event_dto = self._map_dbe_to_dto(dbe=audit_event_dbe)
        return audit_event_dto

    async def query_audit_events(
        self,
        offset: int,
        limit: int,
    ) -> list[AuditEventDTO]:
        filters = []
        audit_events_dbes = await self.audit_event_dao.query(
            filters=filters,
            offset=offset,
            limit=limit,
        )
        audit_events_dtos = [
            self._map_dbe_to_dto(dbe=audit_event_dbe)
            for audit_event_dbe in audit_events_dbes
        ]
        return audit_events_dtos
