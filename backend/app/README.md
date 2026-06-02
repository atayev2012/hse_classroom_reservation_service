# Gateway

FastAPI REST gateway for the React frontend. It talks to the gRPC microservices and
validates JWT access at the edge.

## Responsibilities

- Provides REST routers for auth, notifications, bookings, and schedules.
- Validates access and refresh JWT cookies.
- Refreshes expired access tokens with a valid refresh token.
- Enforces role access rules for student, employee, manager, and admin users.
- Exposes `/health` and service-level health routes under `/api/v1/*/health`.

## Important Files

- `main.py` - FastAPI app, gRPC channels, logging setup.
- `dependencies.py` - auth, JWT, cookie, and role dependencies.
- `health.py` - gateway health-check helper with timeout logging.
- `routers/*/router.py` - REST endpoints.
- `Dockerfile` - builds protobuf contracts and starts Uvicorn.

## Configuration

Required values are listed in the root `.env-example`. The gateway reads service
targets, JWT settings, cookie settings, and CORS origins. Logs are written to
`/app/logs/gateway.log` inside Docker and mounted to root `logs/`.
