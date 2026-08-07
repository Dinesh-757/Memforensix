.PHONY: up down build logs ps migrate test-backend test-frontend clean seed

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

migrate:
	docker compose exec backend alembic upgrade head

test-backend:
	docker compose exec backend pytest -v

test-frontend:
	cd frontend && npm test

seed:
	docker compose exec backend python -m app.utils.seed_demo_data || echo "Seed via scripts/setup.sh instead"

clean:
	docker compose down -v --remove-orphans
	docker system prune -f
