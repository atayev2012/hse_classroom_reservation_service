#!/bin/sh
set -e

cd /app/app
echo "Running booking_service migrations..."
alembic upgrade head

echo "Starting booking_service..."
exec python -m main
