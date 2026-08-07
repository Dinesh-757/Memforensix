# Developer Guide

## Project layout

```
backend/app/
├── core/config.py          Pydantic settings, env-driven
├── models/database.py      SQLAlchemy ORM models + async engine
├── models/schemas.py       Pydantic request/response schemas
├── api/                    FastAPI routers (auth, upload, analysis, results, websocket)
├── services/                Business logic: volatility, yara, ml, analysis orchestration, report
├── workers/                 Celery app + tasks (sync DB session, Redis pub/sub progress)
└── utils/                   security (JWT/hashing), file_utils (upload/hash/format detect)

frontend/src/
├── pages/                  Dashboard, UploadPage, AnalysisView, LoginPage
├── components/              Layout, ProcessTree (D3), NetworkGraph (D3), Timeline, ThreatIndicators, ProgressTracker
├── store/                    Redux Toolkit: authSlice, analysisSlice
├── services/                 api.ts (axios client), websocket.ts (reconnecting WS client)
└── hooks/useAnalysis.ts      WS-to-Redux bridge hook
```

## Adding a new forensics artifact type

1. Add a SQLAlchemy model in `models/database.py` + Pydantic schema in `models/schemas.py`.
2. Extend `AnalysisService.run()` in `services/analysis_service.py` to populate it.
3. Persist it in `workers/tasks.py::run_analysis`.
4. Expose it via `api/results.py`.
5. Add a frontend type in `services/api.ts` and a component/tab in `AnalysisView.tsx`.

## Adding YARA rules

Drop a `.yar`/`.yara` file into `backend/yara_rules/`. Each rule should set `meta.severity` (`low|medium|high|critical`) — the UI colors chips based on this. Rules are compiled once per `YaraService` instance and cached.

## Testing

```bash
cd backend
pytest -v                      # requires Postgres/Redis reachable (see docker-compose.yml)
pytest tests/test_services.py  # pure-unit tests, no DB required
```

Frontend:
```bash
cd frontend
npm run test
```

## Code style

- Backend: type-annotated Python, async SQLAlchemy sessions in the API layer, sync sessions in Celery tasks (workers run outside the event loop).
- Frontend: strict TypeScript, functional components + hooks, Redux Toolkit slices with `createAsyncThunk` for API calls.

## Database migrations

```bash
docker-compose exec backend alembic revision -m "add new table" --autogenerate
docker-compose exec backend alembic upgrade head
```
