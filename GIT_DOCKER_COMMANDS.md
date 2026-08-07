# Git & Docker Commands — MEMFORENSIX

Run these locally after extracting `memforensix.zip`.

## 1. Initialize and push to GitHub

```bash
cd memforensix
git init
git add .
git commit -m "Initial commit: MEMFORENSIX v1.0.0"
git branch -M main
git remote add origin https://github.com/yourusername/memforensix.git
git push -u origin main

# Development branch
git checkout -b development
git push origin development

# Tag the release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 2. Local run with Docker Compose

```bash
cp .env.example .env
cp backend/.env.example backend/.env
# edit backend/.env -> set SECRET_KEY (openssl rand -hex 32)

docker-compose up -d --build
docker-compose exec backend alembic upgrade head

docker-compose logs -f
docker-compose ps
docker-compose down
```

## 3. Build and push images to your own registry

```bash
docker build -t memforensix-backend ./backend
docker build -t memforensix-frontend ./frontend

docker tag memforensix-backend yourusername/memforensix-backend:latest
docker tag memforensix-frontend yourusername/memforensix-frontend:latest

docker login
docker push yourusername/memforensix-backend:latest
docker push yourusername/memforensix-frontend:latest
```

## 4. Production deploy

```bash
cp .env.example .env.production
docker-compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## 5. Run tests

```bash
docker-compose exec backend pytest -v
cd frontend && npm test
```
