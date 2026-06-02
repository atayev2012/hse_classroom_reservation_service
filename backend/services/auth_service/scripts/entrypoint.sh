#!/bin/sh
set -e

cd app
echo "Running auth_service migrations..."
alembic upgrade head

echo "Starting auth_service..."
exec python -m main