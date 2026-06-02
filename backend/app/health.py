from __future__ import annotations

import asyncio
import logging
from typing import Any

import grpc
from fastapi import HTTPException, status

from grpc_utils import proto_to_dict

logger = logging.getLogger(__name__)


async def check_grpc_health(
    stub: Any,
    health_request: Any,
    service_name: str,
    timeout_seconds: float = 3.0,
) -> dict:
    try:
        response = await asyncio.wait_for(
            stub.HealthCheck(health_request),
            timeout=timeout_seconds,
        )
        return proto_to_dict(response)
    except asyncio.TimeoutError as exc:
        logger.exception("%s health check timed out", service_name)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"{service_name} health check timed out",
        ) from exc
    except grpc.aio.AioRpcError as exc:
        logger.exception("%s health check failed: %s", service_name, exc.details())
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service_name} is unavailable",
        ) from exc
    except Exception as exc:
        logger.exception("%s health check failed", service_name)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service_name} health check failed",
        ) from exc
