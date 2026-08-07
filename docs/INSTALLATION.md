# Installation Guide

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- 4GB+ free RAM recommended (Volatility3 analysis of real dumps can be memory-hungry)
- Ports 3000, 8000, 5432, 6379 free on the host

## Steps

1. **Clone and configure**
   ```bash
   git clone <your-repo-url> memforensix
   cd memforensix
   cp .env.example .env
   cp backend/.env.example backend/.env
   ```
   Edit `backend/.env` and set a real `SECRET_KEY`:
   ```bash
   openssl rand -hex 32
   ```

2. **Build and start the stack**
   ```bash
   docker-compose up -d --build
   ```
   This starts: `postgres`, `redis`, `backend` (FastAPI), `worker` (Celery), `frontend` (nginx-served React build).

3. **Run migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Verify**
   ```bash
   curl http://localhost:8000/health
   ```
   Open http://localhost:3000 in a browser.

5. **Create your first user**
   Use the Register form in the UI, or:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","email":"admin@example.com","password":"ChangeMe123!","role":"admin"}'
   ```

## Local (non-Docker) development

**Backend:**
```bash
cd backend
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# requires local Postgres + Redis reachable per backend/.env
alembic upgrade head
uvicorn app.main:app --reload
```

**Celery worker:**
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

- **YARA compile errors on startup**: confirm `backend/yara_rules/*.yar` mounted/copied correctly into the backend container at `/app/yara_rules`.
- **Volatility3 plugin failures**: expected for non-real memory images — the service falls back to synthetic data automatically (see README).
- **WebSocket not updating**: verify the `worker` container can reach `redis` (same Docker network) and that the browser can reach `ws://localhost:8000/api/v1/ws/...` (check nginx/vite proxy config if running frontend dev server separately).
