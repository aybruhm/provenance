from uuid import UUID

from core.escalations.dtos import (
    CreateEscalationDTO,
    EscalationDTO,
    UpdateEscalationDTO,
)
from dbs.postgres.escalations.dbes import EscalationDBE
from dbs.postgres.escalations.interfaces import EscalationDAOInterface


class EscalationService:
    def __init__(self, escalation_dao: EscalationDAOInterface):
        self.escalation_dao = escalation_dao

    def _map_dbe_to_dto(self, dbe: EscalationDBE) -> EscalationDTO:
        return EscalationDTO(
            id=dbe.id,  # type: ignore
            name=dbe.name,  # type: ignore
            tenant_id=dbe.tenant_id,  # type: ignore
            created_at=dbe.created_at,  # type: ignore
            updated_at=dbe.updated_at,  # type: ignore
        )

    def _map_dto_to_dbe(self, dto: CreateEscalationDTO) -> EscalationDBE:
        return EscalationDBE(
            tenant_id=dto.tenant_id,
            agent_id=dto.agent_id,
            action=dto.action,
            parameters_hash=dto.parameters_hash,
            status=dto.status,
            approver_id=dto.approver_id,
            decided_at=dto.decided_at,
            reason=dto.reason,
        )

    async def create_escalation(
        self, create_data: CreateEscalationDTO
    ) -> EscalationDTO:
        escalation_dbe = self._map_dto_to_dbe(dto=create_data)
        escalation_dbe = await self.escalation_dao.create(
            dbe=escalation_dbe,
        )
        escalation_dto = self._map_dbe_to_dto(dbe=escalation_dbe)
        return escalation_dto

    async def get_escalation(self, id: UUID) -> EscalationDTO | None:
        escalation_dbe = await self.escalation_dao.get(id=id)
        if not escalation_dbe:
            return None
        escalation_dto = self._map_dbe_to_dto(dbe=escalation_dbe)
        return escalation_dto

    async def update_escalation(
        self,
        id: UUID,
        update_data: UpdateEscalationDTO,
    ) -> EscalationDTO | None:
        escalation_dbe = await self.escalation_dao.update(
            id=id,
            values_to_update=update_data.model_dump(
                exclude_none=True,
            ),
        )
        if not escalation_dbe:
            return None
        escalation_dto = self._map_dbe_to_dto(dbe=escalation_dbe)
        return escalation_dto

    async def list_escalations(
        self,
        tenant_id: UUID,
        offset: int,
        limit: int,
        status: str | None = None,
    ) -> list[EscalationDTO]:
        filters = [EscalationDBE.tenant_id == tenant_id]
        if status:
            filters.append(EscalationDBE.status == status)

        escalations = await self.query_escalations(
            columns=[EscalationDBE],
            filters=filters,
            offset=offset,
            limit=limit,
        )
        return escalations

    async def query_escalations(
        self,
        columns: list,
        filters: list,
        offset: int,
        limit: int,
    ) -> list[EscalationDTO]:
        filters = []
        escalations_dbes = await self.escalation_dao.query(
            columns=columns,
            filters=filters,
            offset=offset,
            limit=limit,
        )
        escalations_dtos = [
            self._map_dbe_to_dto(dbe=escalation_dbe)
            for escalation_dbe in escalations_dbes
        ]
        return escalations_dtos
