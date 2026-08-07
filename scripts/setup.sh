#!/usr/bin/env bash
# MEMFORENSIX first-time setup script
set -euo pipefail

echo "=== MEMFORENSIX Setup ==="

if ! command -v docker &> /dev/null; then
    echo "Docker is required but not installed. Install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "Docker Compose v2 is required. Install it or upgrade Docker Desktop."
    exit 1
fi

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    SECRET=$(openssl rand -hex 32)
    sed -i.bak "s/generate_with_openssl_rand_hex_32/${SECRET}/" .env && rm -f .env.bak
    echo "Generated a random SECRET_KEY in .env"
fi

if [ ! -f backend/.env ]; then
    cp backend/.env.example backend/.env
fi

echo "Building images..."
docker compose build

echo "Starting services..."
docker compose up -d postgres redis

echo "Waiting for Postgres to be ready..."
sleep 8

echo "Starting backend and running migrations..."
docker compose up -d backend
sleep 5
docker compose exec -T backend alembic upgrade head

echo "Starting remaining services..."
docker compose up -d

echo ""
echo "=== Setup complete ==="
echo "Frontend:  http://localhost"
echo "API docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "Register a user via the UI or:"
echo "  curl -X POST http://localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' \\"
echo "    -d '{\"username\":\"admin\",\"email\":\"admin@example.com\",\"password\":\"ChangeMe123!\",\"role\":\"admin\"}'"
