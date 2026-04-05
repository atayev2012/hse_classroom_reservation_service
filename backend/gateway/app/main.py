from fastapi import FastAPI

from app.auth_router.router import router as auth_router

# Creating a FastAPI app
app = FastAPI(
    title="API Gateway",
    summary="REST API of a Classroom booking service for HSE university"
    )


# Connecting routers
app.include_router(auth_router, prefix="/api/v1/web")
