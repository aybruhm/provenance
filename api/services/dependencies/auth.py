from fastapi import Depends, Request

from middlewares.apikey_auth import APIKeyAuth
from middlewares.jwt_cookie_auth import JWTCookieAuth
from services.dependencies.types import CurrentScopeContext, CurrentUserContext
from services.exceptions import UnauthorizedException


class AuthDependencies:
    """
    Authentication dependencies for FastAPI routes.
    """

    @staticmethod
    def get_current_user(
        request: Request,
        token: str = Depends(JWTCookieAuth()),
    ) -> CurrentUserContext:
        """
        Get the current authenticated user from the request.
        """

        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)

        if not user_id or not username:
            raise UnauthorizedException(detail="User not authenticated")

        user_context = CurrentUserContext(
            id=user_id,
            username=username,
            token=token,
        )
        return user_context

    @staticmethod
    def get_current_scope_from_apikey(
        request: Request,
        token: str = Depends(APIKeyAuth()),
    ) -> CurrentScopeContext:
        """
        Get the current authenticated user from the request using API key authentication.
        """

        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        scope = getattr(request.state, "scope", None)

        if not user_id or not username:
            raise UnauthorizedException(detail="User not authenticated")

        if not scope:
            raise UnauthorizedException(detail="Invalid api-key or revoked api-key")

        scope_context = CurrentScopeContext(
            id=user_id,
            username=username,
            scope=scope,
        )
        return scope_context
