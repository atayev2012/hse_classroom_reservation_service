# Notification Service

Async gRPC service for email notifications and notification history storage.

## Responsibilities

- Sends verification-code, login, booking, and schedule emails.
- Renders HTML templates from `templates/`.
- Records notification attempts in the database.
- Formats date and timestamp template values as Russian dates.
- Exposes a gRPC health check.

## Important Files

- `main.py` - gRPC service implementation.
- `service_modules/email.py` - template rendering and SMTP delivery.
- `service_modules/models.py` - notification history model.
- `service_modules/db_utils.py` - DAO layer.
- `templates/` - HTML email templates.
- `migrations/` - Alembic migrations.
- `Dockerfile` - builds protobuf contracts and starts the container.

## Configuration

Required values are listed in the root `.env-example`. The service reads
`NOTIFICATION_*` database settings and `EMAIL_*` SMTP settings. Logs are written to
`/app/logs/notification_service.log` inside Docker and mounted to root `logs/`.
