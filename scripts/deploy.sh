#!/usr/bin/env bash
# MEMFORENSIX production deployment script
# Usage: ./scripts/deploy.sh [tag]
set -euo pipefail

TAG="${1:-latest}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

echo "=== Deploying MEMFORENSIX (tag: ${TAG}) ==="

if [ ! -f .env ]; then
    echo "Missing .env file. Copy .env.example to .env and set production secrets first."
    exit 1
fi

echo "Pulling latest images..."
docker compose $COMPOSE_FILES pull || echo "Pull skipped (building locally instead)"

echo "Building images..."
docker compose $COMPOSE_FILES build

echo "Running database migrations..."
docker compose $COMPOSE_FILES run --rm backend alembic upgrade head

echo "Starting stack..."
docker compose $COMPOSE_FILES up -d

echo "Waiting for health checks..."
sleep 10
docker compose $COMPOSE_FILES ps

echo "=== Deployment complete ==="
