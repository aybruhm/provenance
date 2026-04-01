from uuid import UUID

from core.agents.dtos import AgentDTO, CreateAgentDTO, UpdateAgentDTO
from dbs.postgres.agents.dbes import AgentDBE
from dbs.postgres.agents.interfaces import AgentDAOInterface


class AgentService:
    def __init__(self, agent_dao: AgentDAOInterface):
        self.agent_dao = agent_dao

    def _map_dbe_to_dto(self, dbe: AgentDBE) -> AgentDTO:
        return AgentDTO(
            id=dbe.id,  # type: ignore
            name=dbe.name,  # type: ignore
            tenant_id=dbe.tenant_id,  # type: ignore
            created_at=dbe.created_at,  # type: ignore
            updated_at=dbe.updated_at,  # type: ignore
        )

    async def create_agent(self, create_data: CreateAgentDTO) -> AgentDTO:
        agent_dbe = await self.agent_dao.create(
            name=create_data.name,
            tenant_id=create_data.tenant_id,
        )
        agent_dto = self._map_dbe_to_dto(dbe=agent_dbe)
        return agent_dto

    async def get_agent(self, id: UUID) -> AgentDTO | None:
        agent_dbe = await self.agent_dao.get(id=id)
        if not agent_dbe:
            return None
        agent_dto = self._map_dbe_to_dto(dbe=agent_dbe)
        return agent_dto

    async def update_agent(
        self,
        id: UUID,
        update_data: UpdateAgentDTO,
    ) -> AgentDTO | None:
        agent_dbe = await self.agent_dao.update(
            id=id,
            values_to_update=update_data.model_dump(
                exclude_none=True,
            ),
        )
        if not agent_dbe:
            return None
        agent_dto = self._map_dbe_to_dto(dbe=agent_dbe)
        return agent_dto

    async def query_agents(
        self,
        offset: int,
        limit: int,
    ) -> list[AgentDTO]:
        filters = []
        agents_dbes = await self.agent_dao.query(
            filters=filters,
            offset=offset,
            limit=limit,
        )
        agents_dtos = [self._map_dbe_to_dto(dbe=agent_dbe) for agent_dbe in agents_dbes]
        return agents_dtos
