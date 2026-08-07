# Deployment Guide

## Production Docker Compose

`docker-compose.prod.yml` builds hardened images (no dev volumes, restart policies, nginx serving a static build) and expects secrets via environment variables rather than `.env` defaults.

```bash
cp .env.example .env.production
# edit .env.production: SECRET_KEY, DB creds, CORS_ORIGINS -> your real domain
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Reverse proxy / TLS

Put nginx or Traefik in front of the `frontend` (port 80) and `backend` (port 8000) containers, terminate TLS there, and proxy:
- `/` → frontend:80
- `/api` and `/api/v1/ws` → backend:8000 (WebSocket upgrade headers required)

## Scaling

- Scale Celery workers horizontally: `docker-compose up -d --scale worker=4`
- Volatility3 analysis is CPU/memory intensive on real dumps — size worker nodes accordingly and consider a dedicated worker pool separate from the API tier.
- Postgres and Redis should be managed services in production (RDS/CloudSQL, ElastiCache/MemoryStore) rather than containers, for durability.

## Backups

- `pg_dump` the `memforensix` database on a schedule.
- Uploaded dumps live in the `backend_uploads` volume (or your configured `UPLOAD_DIR`) — back this up or move to S3-compatible object storage for production (would require extending `file_utils.py`'s save path).

## Environment checklist before going live

- [ ] Unique, random `SECRET_KEY`
- [ ] `DEBUG=false`
- [ ] `CORS_ORIGINS` restricted to real frontend origin(s)
- [ ] Postgres/Redis not exposed publicly (internal Docker network only)
- [ ] TLS terminated in front of both services
- [ ] Log aggregation configured (the app logs structured request lines to stdout)
