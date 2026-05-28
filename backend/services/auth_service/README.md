# Auth Service

Async gRPC service for user login, verification-code auth, JWT refresh, and user CRUD.

## Responsibilities

- Stores users, student profiles, employee profiles, and verification codes.
- Sends verification and successful-login notifications through `notification_service`.
- Issues access and refresh JWT tokens.
- Exposes gRPC health checks for Docker and the gateway.

## Important Files

- `main.py` - gRPC service implementation.
- `service_modules/models.py` - SQLAlchemy models.
- `service_modules/db_utils.py` - DAO layer.
- `service_modules/config.py` - database, JWT, service, and logging settings.
- `migrations/` - Alembic migrations.
- `scripts/entrypoint.sh` - runs migrations before service startup.
- `Dockerfile` - builds protobuf contracts and starts the container.

## Configuration

Required values are listed in the root `.env-example`. The service reads `AUTH_*`,
`NOTIFICATION_SERVICE_*`, and JWT settings. Logs are written to `/app/logs/auth_service.log`
inside Docker and mounted to the root `logs/` directory by compose.
