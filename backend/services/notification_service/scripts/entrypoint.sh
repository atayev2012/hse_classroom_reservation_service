#!/bin/sh
set -e

cd /app/app
echo "Running notification_service migrations..."
alembic upgrade head

echo "Starting notification_service..."
exec python -m main
