from fastapi import FastAPI

from app.auth_router.router import router as auth_router
from app.reservation_router.router import router as room_reserv_router

# Creating a FastAPI app
app = FastAPI(
    title="API Gateway",
    summary="REST API of a Classroom booking service for HSE university"
    )

v1_web_api_prefix = "/api/v1/web"

# Connecting routers
app.include_router(auth_router, prefix=v1_web_api_prefix)
app.include_router(room_reserv_router, prefix=v1_web_api_prefix)
