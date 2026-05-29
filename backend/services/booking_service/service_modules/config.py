from __future__ import annotations

from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from os import getenv

from dotenv import load_dotenv

load_dotenv()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": StreamHandler,
            "formatter": "simple",
            "level": "INFO",
        },
        "file": {
            "class": RotatingFileHandler,
            "formatter": "simple",
            "filename": "logs/booking_service.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}


class DatabaseConfig:
    def __init__(self):
        self.DB_URL = getenv("BOOKING_DB_URL")
        self.DB_USERNAME = getenv("BOOKING_DB_USERNAME")
        self.DB_PASSWORD = getenv("BOOKING_DB_PASSWORD")
        self.DB_HOST = getenv("BOOKING_DB_HOST")
        self.DB_PORT = getenv("BOOKING_DB_PORT")
        self.DB_NAME = getenv("BOOKING_DB_NAME")

    def get_db_url(self) -> str:
        if self.DB_URL:
            return self.DB_URL

        if not all(
            [
                self.DB_USERNAME,
                self.DB_PASSWORD,
                self.DB_HOST,
                self.DB_PORT,
                self.DB_NAME,
            ]
        ):
            return "sqlite+aiosqlite:///:memory:"

        return f"postgresql+asyncpg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class ServiceConfig:
    def __init__(self):
        self.HOST = getenv("BOOKING_SERVICE_HOST", "0.0.0.0")
        self.PORT = int(getenv("BOOKING_SERVICE_PORT", "5535"))


db_config = DatabaseConfig()
service_config = ServiceConfig()
