from fastapi import Depends, Request

from middlewares.apikey_auth import _API_KEY_HEADER_NAME, APIKeyAuth
from middlewares.jwt_cookie_auth import JWTCookieAuth
from services.dependencies.types import CurrentScopeContext, CurrentUserContext
from services.exceptions import UnauthorizedException

# Module-level singletons with auto_error=False so they return None
# instead of raising when the credential is simply absent
_jwt_auth = JWTCookieAuth(auto_error=False)
_apikey_auth = APIKeyAuth(auto_error=False)


class AuthDependencies:
    """
    Authentication dependencies for FastAPI routes.
    """

    @staticmethod
    def get_current_user(
        request: Request,
        token: str = Depends(_jwt_auth),
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
        token: str = Depends(_apikey_auth),
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

    @staticmethod
    async def get_authenticated(request: Request) -> None:
        """
        Accepts either an API key (X-PROVENANCE-API-KEY header)
        or a JWT session cookie (access_token). API key takes precedence.
        """

        if request.headers.get(_API_KEY_HEADER_NAME.lower()):
            await _apikey_auth(request)

        elif request.cookies.get("access_token"):
            await _jwt_auth(request)

        else:
            raise UnauthorizedException(
                detail="Authentication required. Provide an API key or a valid session token."
            )
