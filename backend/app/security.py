from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status

from config import settings


def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    return payload


def create_access_token(payload: dict[str, Any]) -> str:
    token_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"exp", "iat", "type"}
    }
    token_payload["iat"] = datetime.now(timezone.utc)
    token_payload["exp"] = token_payload["iat"] + timedelta(
        minutes=settings.jwt_access_expire_minutes
    )
    token_payload["type"] = "access"

    return jwt.encode(
        token_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
