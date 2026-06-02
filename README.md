# HSE Booking Platform

Dockerized microservice web app for HSE classroom schedules, room bookings, users,
and email notifications.

## Documentation

- [Auth service](backend/services/auth_service/README.md)
- [Notification service](backend/services/notification_service/README.md)
- [Booking service](backend/services/booking_service/README.md)
- [Schedule service](backend/services/schedule_service/README.md)
- [Gateway](backend/app/README.md)
- [Frontend](frontend/README.md)
- [Deployment guide](docs/DEPLOYMENT.md)

## Run Locally

1. Copy `.env-example` to `.env` and fill SMTP/JWT/database secrets.
2. Build and start everything:

```bash
docker compose up --build
```

3. Open the frontend:

```text
http://localhost:5173
```

The frontend calls the gateway through `/api/v1`. The gateway connects to the gRPC
services on the Docker network. Alembic migrations run from each service entrypoint.

## Logs

All Python containers write service logs into the root `logs/` directory:

- `logs/auth_service.log`
- `logs/notification_service.log`
- `logs/booking_service.log`
- `logs/schedule_service.log`
- `logs/gateway.log`

## Useful Commands

```bash
docker compose ps
docker compose logs gateway
docker compose logs frontend
docker compose down
```
