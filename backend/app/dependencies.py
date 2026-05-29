from __future__ import annotations

from collections.abc import Callable

import auth_service_pb2
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings
from grpc_utils import proto_to_dict
from security import decode_token

ACCESS_TOKEN_COOKIE = "hse_access_token"
REFRESH_TOKEN_COOKIE = "hse_refresh_token"

bearer_scheme = HTTPBearer(auto_error=False)


def _set_cookie(response: Response, key: str, value: str, max_age: int) -> None:
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )


def set_token_cookies(
    response: Response,
    access_token: str,
    refresh_token: str | None = None,
) -> None:
    _set_cookie(
        response,
        ACCESS_TOKEN_COOKIE,
        access_token,
        settings.jwt_access_expire_minutes * 60,
    )
    if refresh_token:
        _set_cookie(
            response,
            REFRESH_TOKEN_COOKIE,
            refresh_token,
            settings.jwt_refresh_expire_days * 24 * 60 * 60,
        )


def clear_token_cookies(response: Response) -> None:
    for key in (ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE):
        response.delete_cookie(
            key=key,
            domain=settings.cookie_domain,
            path="/",
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
        )


def _get_access_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials:
        return credentials.credentials
    return request.cookies.get(ACCESS_TOKEN_COOKIE)


def _get_refresh_token(request: Request) -> str | None:
    return (
        request.cookies.get(REFRESH_TOKEN_COOKIE)
        or request.headers.get("x-refresh-token")
    )


async def issue_access_token_from_refresh(
    request: Request,
    refresh_token: str,
) -> tuple[dict, str]:
    refresh_payload = decode_token(refresh_token, expected_type="refresh")
    user_id = refresh_payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is missing user_id",
        )

    refresh_response = await request.app.state.auth_stub.RefreshToken(
        auth_service_pb2.RefreshTokenRequest(user_id=int(user_id))
    )
    if not refresh_response.success or not refresh_response.access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=refresh_response.status or "Unable to refresh access token",
        )

    access_payload = decode_token(refresh_response.access_token, expected_type="access")
    return access_payload, refresh_response.access_token


async def refresh_access_token(
    request: Request,
    response: Response,
    refresh_token: str,
) -> dict:
    access_payload, access_token = await issue_access_token_from_refresh(
        request,
        refresh_token,
    )
    set_token_cookies(response, access_token)
    return access_payload


async def get_token_payload(
    request: Request,
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    access_token = _get_access_token(request, credentials)
    if not access_token:
        refresh_token = _get_refresh_token(request)
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing access token",
            )
        return await refresh_access_token(request, response, refresh_token)

    try:
        return decode_token(access_token, expected_type="access")
    except HTTPException as exc:
        if exc.detail != "Token has expired":
            raise

    refresh_token = _get_refresh_token(request)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    return await refresh_access_token(request, response, refresh_token)


async def get_current_user(
    request: Request,
    payload: dict = Depends(get_token_payload),
) -> dict:
    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing user_id",
        )

    response = await request.app.state.auth_stub.GetSingleUser(
        auth_service_pb2.User(id=int(user_id))
    )

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=response.status,
        )

    user = proto_to_dict(response.user)
    user["role"] = user.get("type")
    return user


def require_roles(*roles: str) -> Callable:
    async def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user

    return dependency
