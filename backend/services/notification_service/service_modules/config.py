from dotenv import load_dotenv
from os import getenv
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

load_dotenv()

# Logging configurations
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
            "filename": "logs/notification_service.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,      # Keep 5 old log files
            "level": "INFO",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    }
}

# Configuration class
class DatabaseConfig:
    def __init__(self):
        self.DB_URL = getenv("NOTIFICATION_DB_URL")
        self.DB_USERNAME = getenv("NOTIFICATION_DB_USERNAME")
        self.DB_PASSWORD = getenv("NOTIFICATION_DB_PASSWORD")
        self.DB_HOST = getenv("NOTIFICATION_DB_HOST")
        self.DB_PORT = getenv("NOTIFICATION_DB_PORT")
        self.DB_NAME = getenv("NOTIFICATION_DB_NAME")

    def get_db_url(self) -> str:
        """
        Construct the database connection URL from configuration data
        """
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
        self.HOST = getenv("NOTIFICATION_SERVICE_HOST", "0.0.0.0")
        self.PORT = int(
            getenv(
                "NOTIFICATION_SERVICE_PORT",
                getenv("NOTIFICAITON_SERVICE_PORT", "5533"),
            )
        )


class EmailConfig:
    def __init__(self):
        self.HOST = getenv("EMAIL_HOST", "localhost")
        self.PORT = int(getenv("EMAIL_PORT", "25"))
        self.USERNAME = getenv("EMAIL_USERNAME")
        self.PASSWORD = getenv("EMAIL_PASSWORD")
        self.FROM_EMAIL = getenv("EMAIL_ADDRESS", "no-reply@example.com")
        self.FROM_NAME = getenv("EMAIL_FROM_NAME", "HSE Schedule")
        self.USE_TLS = getenv("EMAIL_USE_TLS", "false").lower() in ["true", "1", "yes"]
        self.USE_SSL = getenv("EMAIL_USE_SSL", "false").lower() in ["true", "1", "yes"]
        self.TIMEOUT = float(getenv("EMAIL_TIMEOUT_SECONDS", "15"))


# Creation of configuration samples
db_config = DatabaseConfig()
service_config = ServiceConfig()
email_config = EmailConfig()
