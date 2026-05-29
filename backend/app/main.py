from __future__ import annotations

import logging
import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

import auth_service_pb2_grpc
import booking_service_pb2_grpc
import grpc
import notification_service_pb2_grpc
import schedule_service_pb2_grpc
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.auth.router import router as auth_router
from routers.booking.router import router as booking_router
from routers.notification.router import router as notification_router
from routers.schedule.router import router as schedule_router

Path("logs").mkdir(exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "logs/gateway.log",
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Opening gateway gRPC channels")
    app.state.auth_channel = grpc.aio.insecure_channel(settings.auth_target)
    app.state.notification_channel = grpc.aio.insecure_channel(
        settings.notification_target
    )
    app.state.booking_channel = grpc.aio.insecure_channel(settings.booking_target)
    app.state.schedule_channel = grpc.aio.insecure_channel(settings.schedule_target)

    app.state.auth_stub = auth_service_pb2_grpc.AuthServiceStub(app.state.auth_channel)
    app.state.notification_stub = (
        notification_service_pb2_grpc.NotificationServiceStub(
            app.state.notification_channel
        )
    )
    app.state.booking_stub = booking_service_pb2_grpc.BookingServiceStub(
        app.state.booking_channel
    )
    app.state.schedule_stub = schedule_service_pb2_grpc.ScheduleServiceStub(
        app.state.schedule_channel
    )

    yield

    logger.info("Closing gateway gRPC channels")
    await app.state.auth_channel.close()
    await app.state.notification_channel.close()
    await app.state.booking_channel.close()
    await app.state.schedule_channel.close()


app = FastAPI(
    title="HSE Classroom Platform API Gateway",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = "/api/v1"

app.include_router(auth_router, prefix=api_prefix)
app.include_router(notification_router, prefix=api_prefix)
app.include_router(booking_router, prefix=api_prefix)
app.include_router(schedule_router, prefix=api_prefix)


@app.get("/health")
async def health():
    return {"success": True, "status": "SERVING"}
