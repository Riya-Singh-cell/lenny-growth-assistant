import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoints(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Health check
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "Lenny" in data["app_name"]

        # Readiness check
        ready_res = await client.get("/ready")
        assert ready_res.status_code == 200
        ready_data = ready_res.json()
        assert "database" in ready_data
        assert "llm_provider" in ready_data
        assert "vector_store" in ready_data


@pytest.mark.asyncio
async def test_session_lifecycle_api(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create session
        create_res = await client.post("/api/sessions", json={"title": "Evaluator Test Session"})
        assert create_res.status_code == 201
        session_data = create_res.json()
        session_id = session_data["id"]
        assert session_data["title"] == "Evaluator Test Session"

        # 2. List sessions
        list_res = await client.get("/api/sessions")
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert any(s["id"] == session_id for s in sessions)

        # 3. Get session detail
        detail_res = await client.get(f"/api/sessions/{session_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == session_id
        assert "messages" in detail
        assert "artifacts" in detail

        # 4. Delete session
        del_res = await client.delete(f"/api/sessions/{session_id}")
        assert del_res.status_code == 204

        # 5. Verify deleted
        get_after_del = await client.get(f"/api/sessions/{session_id}")
        assert get_after_del.status_code == 404


@pytest.mark.asyncio
async def test_validation_failure_handling(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Send invalid payload missing required fields
        res = await client.post("/api/chat", json={"invalid_field": 123})
        assert res.status_code == 422
