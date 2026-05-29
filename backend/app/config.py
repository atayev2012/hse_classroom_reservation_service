from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


def env_int(name: str, default: str) -> int:
    return int(getenv(name) or default)


def env_bool(name: str, default: str = "false") -> bool:
    return (getenv(name) or default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    gateway_host: str = getenv("GATEWAY_HOST", "0.0.0.0")
    gateway_port: int = env_int("GATEWAY_PORT", "8000")

    auth_service_host: str = getenv("AUTH_SERVICE_HOST", "auth_service")
    auth_service_port: int = env_int("AUTH_SERVICE_PORT", "5534")
    notification_service_host: str = getenv(
        "NOTIFICATION_SERVICE_HOST",
        "notification_service",
    )
    notification_service_port: int = int(
        getenv("NOTIFICATION_SERVICE_PORT")
        or getenv("NOTIFICAITON_SERVICE_PORT")
        or "5533"
    )
    booking_service_host: str = getenv("BOOKING_SERVICE_HOST", "booking_service")
    booking_service_port: int = env_int("BOOKING_SERVICE_PORT", "5535")
    schedule_service_host: str = getenv("SCHEDULE_SERVICE_HOST", "schedule_service")
    schedule_service_port: int = env_int("SCHEDULE_SERVICE_PORT", "5536")

    jwt_secret_key: str = getenv("AUTH_JWT_SECRET_KEY", "dev-secret")
    jwt_algorithm: str = getenv("AUTH_JWT_ALGORITHM", "HS256")
    jwt_access_expire_minutes: int = env_int("AUTH_JWT_ACCESS_EXPIRE_MINUTES", "15")
    jwt_refresh_expire_days: int = env_int("AUTH_JWT_REFRESH_EXPIRE_DAYS", "30")

    cookie_secure: bool = env_bool("AUTH_COOKIE_SECURE", "false")
    cookie_samesite: str = getenv("AUTH_COOKIE_SAMESITE", "lax")
    cookie_domain: str | None = getenv("AUTH_COOKIE_DOMAIN") or None
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in (getenv("GATEWAY_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")).split(",")
        if origin.strip()
    )

    @property
    def auth_target(self) -> str:
        return f"{self.auth_service_host}:{self.auth_service_port}"

    @property
    def notification_target(self) -> str:
        return f"{self.notification_service_host}:{self.notification_service_port}"

    @property
    def booking_target(self) -> str:
        return f"{self.booking_service_host}:{self.booking_service_port}"

    @property
    def schedule_target(self) -> str:
        return f"{self.schedule_service_host}:{self.schedule_service_port}"


settings = Settings()
