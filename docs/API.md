# API Documentation

Base URL: `http://localhost:8000/api/v1`
Interactive OpenAPI/Swagger docs: `http://localhost:8000/api/v1/docs`

All endpoints except `/auth/register` and `/auth/login` require a Bearer JWT:
```
Authorization: Bearer <access_token>
```

## Auth

### `POST /auth/register`
```json
{ "username": "analyst1", "email": "a@example.com", "password": "SecurePass123!", "role": "analyst" }
```
`201` → user object.

### `POST /auth/login`
```json
{ "username": "analyst1", "password": "SecurePass123!" }
```
`200` →
```json
{ "access_token": "...", "refresh_token": "...", "token_type": "bearer" }
```

### `GET /auth/me`
Returns the authenticated user's profile.

## Upload

### `POST /upload`  (multipart/form-data, field `file`)
Accepts `.raw .dmp .mem .vmem .elf .core`. Saves the dump, creates an `Analysis` row (`status=queued`), and enqueues a Celery task. Returns the `Analysis` object immediately; poll or use WebSocket for progress.

## Analyses

- `GET /analyses?page=1&page_size=20` — paginated list for the current user
- `GET /analyses/{id}` — single analysis status
- `DELETE /analyses/{id}` — admin/analyst only

## Results

- `GET /results/{id}` — full results: processes, connections, YARA matches, ML findings, summary
- `GET /results/{id}/export?format=json|csv|pdf` — downloadable report

## WebSocket

`ws://localhost:8000/api/v1/ws/analysis/{analysis_id}`

Server pushes frames:
```json
{ "type": "progress", "analysis_id": "...", "status": "running", "progress": 45, "stage": "yara", "message": "Scanning memory image against YARA ruleset" }
```

## Error format

```json
{ "detail": "human readable message" }
```
Standard HTTP status codes: `400` validation, `401` unauthenticated, `403` insufficient role, `404` not found, `413` file too large, `500` internal error.
