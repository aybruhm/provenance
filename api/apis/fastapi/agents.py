import traceback
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from apis.fastapi.dtos import (
    AgentCreateRequestDTO,
    AgentListResponseDTO,
    AgentResponseDTO,
    AgentUpdateRequestDTO,
)
from core.agents.service import AgentService
from services.dependencies import get_current_user
from services.exceptions import (
    BadRequestException,
    InternalServerErrorException,
    NotFoundException,
)
from utils.logger_utils import logger


class AgentAPIRouter:
    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service

        # Initialize api router
        self.router = APIRouter(
            dependencies=[Depends(get_current_user)],
        )

        # Register routes
        self.router.add_api_route(
            "/",
            self.create_agent,
            methods=["POST"],
            response_model=AgentResponseDTO,
        )
        self.router.add_api_route(
            "/",
            self.get_agents,
            methods=["GET"],
            response_model=AgentListResponseDTO,
        )
        self.router.add_api_route(
            "/{agent_id}",
            self.get_agent,
            methods=["GET"],
            response_model=AgentResponseDTO,
        )
        self.router.add_api_route(
            "/{agent_id}",
            self.update_agent,
            methods=["PUT"],
            response_model=AgentResponseDTO,
        )

    async def create_agent(
        self, request: Request, agent_create_dto: AgentCreateRequestDTO
    ) -> AgentResponseDTO:
        try:
            agent = await self.agent_service.create_agent(create_data=agent_create_dto)
            return AgentResponseDTO(agent=agent)
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to create tenant")

    async def get_agents(
        self,
        request: Request,
        offset: int = Query(0),
        limit: int = Query(100),
    ) -> AgentListResponseDTO:
        try:
            agents = await self.agent_service.query_agents(
                offset=offset,
                limit=limit,
            )
            return AgentListResponseDTO(agents=agents)
        except Exception as e:
            logger.error(f"Failed to get tenants: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to get tenants")

    async def get_agent(self, request: Request, agent_id: str) -> AgentResponseDTO:
        try:
            agent = await self.agent_service.get_agent(id=UUID(agent_id))
            if not agent:
                raise NotFoundException(detail="Agent not found")
            return AgentResponseDTO(agent=agent)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get agent: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to get agent")

    async def update_agent(
        self,
        request: Request,
        agent_id: str,
        agent_update_dto: AgentUpdateRequestDTO,
    ) -> AgentResponseDTO:
        try:
            agent = await self.agent_service.update_agent(
                id=UUID(agent_id),
                update_data=agent_update_dto,
            )
            if not agent:
                raise NotFoundException(detail="Agent not found")
            return AgentResponseDTO(agent=agent)
        except ValueError as e:
            raise BadRequestException(detail=str(e))
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to update agent: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise InternalServerErrorException(detail="Failed to update agent")
