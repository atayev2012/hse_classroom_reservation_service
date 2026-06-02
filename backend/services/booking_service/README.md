# Booking Service

Async gRPC service for buildings, rooms, equipment, and room bookings.

## Responsibilities

- Manages building, room, equipment, and booking CRUD.
- Prevents overlapping active room bookings.
- Keeps schedule-created booking events traceable through schedule item metadata.
- Exposes a gRPC health check.

## Important Files

- `main.py` - gRPC service implementation.
- `service_modules/models.py` - SQLAlchemy models.
- `service_modules/db_utils.py` - DAO layer.
- `migrations/` - Alembic migrations.
- `Dockerfile` - builds protobuf contracts and starts the container.

## Configuration

Required values are listed in the root `.env-example`. The service reads `BOOKING_*`
database and service settings. Logs are written to `/app/logs/booking_service.log`
inside Docker and mounted to root `logs/`.
