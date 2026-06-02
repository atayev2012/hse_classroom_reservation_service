#!/bin/sh
set -e

cd /app/app
echo "Running schedule_service migrations..."
alembic upgrade head

echo "Starting schedule_service..."
exec python -m main
