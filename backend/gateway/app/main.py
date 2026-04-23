import grpc
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import config

from app.auth_router.router import router as auth_router
from app.reservation_router.router import router as room_reserv_router
import auth_service_pb2, auth_service_pb2_grpc, \
        notification_service_pb2, notification_service_pb2_grpc

# Creating connections to all of the microservices
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the gRPC channels
    # AUTH service
    app.state.channel_auth = grpc.aio.insecure_channel(f"localhost:{config.auth_port}")
    app.state.stub_auth = auth_service_pb2_grpc.AuthServiceStub(app.state.channel_auth)

    # NOTIFICATOIN service
    app.state.channel_notification = grpc.aio.insecure_channel(f"localhost:{config.notification_port}")
    app.state.stub_notification = notification_service_pb2_grpc.NotificationServiceStub(app.state.channel_notification)
    
    yield

    # Shutdown: Close the channels
    await app.state.channel_auth.close()
    await app.state.channel_notification.close()


# Creating a FastAPI app
app = FastAPI(
    title="API Gateway",
    summary="REST API of a Classroom booking service for HSE university",
    lifespan=lifespan
    )

v1_web_api_prefix = "/api/v1/web"

# Connecting routers
app.include_router(auth_router, prefix=v1_web_api_prefix)
app.include_router(room_reserv_router, prefix=v1_web_api_prefix)
