import traceback
from uuid import UUID

from fastapi import HTTPException, Request
from fastapi.security import APIKeyHeader

from core.api_keys import utils
from core.api_keys.service import APIKeyService
from dbs.postgres.api_keys.dao import APIKeyDAO
from services.exceptions import InternalServerErrorException, UnauthorizedException
from utils.logger_utils import logger

# Private configurations
_API_KEY_HEADER_NAME = "X-PROVENANCE-API-KEY"


class APIKeyAuth(APIKeyHeader):
    def __init__(
        self,
        name: str = _API_KEY_HEADER_NAME,
        scheme_name: str | None = None,
        description: str | None = None,
        auto_error: bool = True,
    ):
        self.apikey_service = APIKeyService(APIKeyDAO())
        super().__init__(
            name=name,
            scheme_name=scheme_name,
            description=description,
            auto_error=auto_error,
        )

    def _parse_api_key(self, api_key: str) -> str:
        """Parse the api key into a prefix and key hash."""

        parts = api_key.split("_", 2)
        if len(parts) != 3:
            raise UnauthorizedException(detail="Invalid api-key format.")

        pk, environment, body = parts
        prefix = f"{pk}_{environment}_{body[:8]}"
        return prefix

    async def __call__(self, request: Request):
        try:
            api_key = await super().__call__(request)
            if not api_key:
                raise UnauthorizedException(
                    detail=f"Invalid authentication scheme. Expected {_API_KEY_HEADER_NAME} from header.",
                )

            # Verify api key
            is_valid = await self.verify_api_key(
                request=request,
                token=api_key,
            )
            if not is_valid:
                raise UnauthorizedException(
                    detail="Invalid api-key or revoked api-key."
                )

            return api_key
        except UnauthorizedException as e:
            raise e
        except HTTPException as e:
            raise UnauthorizedException(detail="Not authenticated") from e
        except Exception:
            logger.error("Authentication error: %s", traceback.format_exc())
            raise InternalServerErrorException(
                detail="Authentication failed due to an internal error."
            )

    async def verify_api_key(self, request: Request, token: str) -> bool:
        try:
            # Parse api key and retrieve the corresponding record from database
            prefix = self._parse_api_key(token)
            apikey_dto = await self.apikey_service.get_by_prefix(prefix=prefix)
            if not apikey_dto:
                return False

            # Compare the digest of the incoming key against the stored hash
            is_valid = utils.verify_api_key(
                incoming_key=token,
                stored_hash=apikey_dto.key_hash,
            )
            if not is_valid:
                return False

            # Set user context in request state
            request.state.user_id = UUID(apikey_dto.created_by.id)
            request.state.username = apikey_dto.created_by.username
            request.state.scope = UUID(apikey_dto.scope)  # scope -> tenant_policy_id

            return is_valid
        except UnauthorizedException:
            return False
        except Exception:
            logger.error("Verification error: %s", traceback.format_exc())
            return False
