# Schedule Service

Async gRPC service for academic calendars, programmes, groups, courses, and schedules.

## Responsibilities

- Manages academic years, modules, holidays, programmes, groups, courses, and schedule items.
- Keeps schedules in draft until published.
- Checks booking conflicts through `booking_service`.
- Registers published schedule items as booking events and keeps `booking_id` links.
- Updates student group names through `auth_service`.
- Exposes a gRPC health check.

## Important Files

- `main.py` - gRPC service implementation and inter-service clients.
- `service_modules/models.py` - SQLAlchemy models.
- `service_modules/db_utils.py` - DAO layer.
- `migrations/` - Alembic migrations.
- `Dockerfile` - builds protobuf contracts and starts the container.

## Configuration

Required values are listed in the root `.env-example`. The service reads `SCHEDULE_*`,
`AUTH_SERVICE_*`, and `BOOKING_SERVICE_*` settings. Logs are written to
`/app/logs/schedule_service.log` inside Docker and mounted to root `logs/`.
