"""
API test suite. Uses httpx.AsyncClient against the FastAPI app.
Requires a running Postgres/Redis (see docker-compose.test.yml or
run against the dockerized stack) — these are integration-style
tests reflecting the real dependency graph of the app rather than
fully mocked unit tests.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert "message" in resp.json()


@pytest.mark.asyncio
async def test_register_and_login(client):
    payload = {
        "username": "test_analyst",
        "email": "analyst@example.com",
        "password": "SecurePass123!",
        "role": "analyst",
    }
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code in (201, 400)  # 400 if already registered from prior run

    login_resp = await client.post("/api/v1/auth/login", json={
        "username": "test_analyst", "password": "SecurePass123!",
    })
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent_user", "password": "wrong",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_upload_requires_auth(client):
    resp = await client.post("/api/v1/upload", files={"file": ("test.raw", b"fake-data")})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_list_analyses_requires_auth(client):
    resp = await client.get("/api/v1/analyses")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_upload_rejects_bad_extension(client):
    login_resp = await client.post("/api/v1/auth/login", json={
        "username": "test_analyst", "password": "SecurePass123!",
    })
    token = login_resp.json()["access_token"]
    resp = await client.post(
        "/api/v1/upload",
        files={"file": ("malicious.exe", b"not-a-dump")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
