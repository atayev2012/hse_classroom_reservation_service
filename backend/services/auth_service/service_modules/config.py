from dotenv import load_dotenv
from os import getenv
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone, timedelta
import jwt

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
            # "filename": "/app/logs/auth_service.log",
            "filename": "logs/auth_service.log",
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
        self.DB_URL = getenv("AUTH_DB_URL")
        self.DB_USERNAME = getenv("AUTH_DB_USERNAME")
        self.DB_PASSWORD = getenv("AUTH_DB_PASSWORD")
        self.DB_HOST = getenv("AUTH_DB_HOST")
        self.DB_PORT = getenv("AUTH_DB_PORT")
        self.DB_NAME = getenv("AUTH_DB_NAME")

    def get_db_url(self) -> str:
        """
        Construct the database connection URL from configuration data
        """
        if self.DB_URL:
            return self.DB_URL

        return f"postgresql+asyncpg://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class ServiceConfig:
    def __init__(self):
        self.HOST = getenv("AUTH_SERVICE_HOST", "0.0.0.0")
        self.PORT = int(getenv("AUTH_SERVICE_PORT", "5534"))
        self.NOTIFICATION_SERVICE_HOST = getenv(
            "NOTIFICATION_SERVICE_HOST",
            "notification_service",
        )
        self.NOTIFICATION_SERVICE_PORT = int(
            getenv(
                "NOTIFICATION_SERVICE_PORT",
                getenv("NOTIFICAITON_SERVICE_PORT", "5533"),
            )
        )
        self.VERIFICATION_URL = getenv(
            "AUTH_VERIFICATION_URL",
            "http://localhost/verify",
        )
        self.VERIFICATION_CODE_VALID_MINUTES = int(
            getenv("AUTH_VERIFICATION_CODE_VALID_MINUTES", "10")
        )


class JWTConfig:
    def __init__(self):
        self.AUTH_JWT_SECRET_KEY = getenv("AUTH_JWT_SECRET_KEY", "dev-secret")
        self.AUTH_JWT_ALGORITHM = getenv("AUTH_JWT_ALGORITHM", "HS256")
        self.AUTH_JWT_ACCESS_EXPIRE_MINUTES = int(
            getenv("AUTH_JWT_ACCESS_EXPIRE_MINUTES", "15")
        )
        self.AUTH_JWT_REFRESH_EXPIRE_DAYS = int(
            getenv("AUTH_JWT_REFRESH_EXPIRE_DAYS", "30")
        )
    
    def generate_token(self, payload_data: dict, token_type: str = "access") -> str:
        payload = payload_data.copy()
        
        payload["iat"] = datetime.now(timezone.utc)
        payload["type"] = token_type

        if token_type == "access":
            payload["exp"] = payload["iat"] + timedelta(minutes=self.AUTH_JWT_ACCESS_EXPIRE_MINUTES)
        elif token_type == "refresh":
            payload["exp"] = payload["iat"] + timedelta(days=self.AUTH_JWT_REFRESH_EXPIRE_DAYS)

        return jwt.encode(payload=payload, key=self.AUTH_JWT_SECRET_KEY, algorithm=self.AUTH_JWT_ALGORITHM)


class JWTToken:
    def __init__(self):
        self.payload: dict | None = None
        
        self.token: str | None = None
        self.is_valid: bool | None = None
        self.is_expired: bool | None = None
    
    # create new jwt token
    def generate_token(self, payload_data: dict, token_type: str = "access") -> str:
        self.payload = payload_data.copy()
        self.payload["type"] = token_type
        self.payload["iat"] = datetime.now(timezone.utc)
    
        if token_type == "access":
            self.payload["exp"] = self.payload["iat"] + timedelta(minutes=jwt_config.AUTH_JWT_ACCESS_EXPIRE_MINUTES)
        elif token_type == "refresh":
            self.payload["exp"] = self.payload["iat"] + timedelta(days=jwt_config.AUTH_JWT_REFRESH_EXPIRE_DAYS)

        self.token = jwt.encode(
            payload=self.payload, 
            key=jwt_config.AUTH_JWT_SECRET_KEY, 
            algorithm=jwt_config.AUTH_JWT_ALGORITHM
            )
        
        self.is_valid = True
        self.is_expired = False
        
        return self.token

    # decode from existing jwt token
    def decode_from_token(self, jwt_token: str) -> dict | None:
        try:
            self.payload = jwt.decode(
                jwt=jwt_token, 
                key=jwt_config.AUTH_JWT_SECRET_KEY, 
                algorithms=[jwt_config.AUTH_JWT_ALGORITHM]
                )
            
            self.token = jwt_token
            self.is_valid = True
            self.is_expired = False

            return self.payload

        except jwt.ExpiredSignatureError:
            print("Expired")
            self.is_valid = False
            self.is_expired = True

        except jwt.InvalidSignatureError:
            print("Invalid signature")
            self.is_valid = False

        except jwt.InvalidTokenError:
            print("Invalid token")
            self.is_valid = False
        
        return None

# Creation of configuration samples
db_config = DatabaseConfig()
jwt_config = JWTConfig()
service_config = ServiceConfig()
