"""
Integration-тесты для rehearsal endpoints.
GET /rehearsals/{id}, GET /rehearsals/student/{id}
POST /rehearsals/, POST /rehearsals/{id}/cancel
"""

import pytest
import httpx
from httpx import ASGITransport
from datetime import datetime, timezone, timedelta

from src.main import create_app
from src.utils.security import create_token



@pytest.fixture
async def app(session):
    _app = create_app()
    from src.core.database import get_session

    async def override_get_session():
        yield session

    _app.dependency_overrides[get_session] = override_get_session
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def student_client(app, test_student):
    token = create_token({"sub": str(test_student.id), "role": "STUDENT"})
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.cookies.set("jwt_token", token, domain="test")
        yield ac


@pytest.fixture
async def test_rehearsal_data(test_room, test_student):
    """Данные для создания репетиции."""
    now = datetime.now(timezone.utc)
    return {
        "room_id": test_room.id,
        "student_id": test_student.id,
    }


class TestGetRehearsal:
    @pytest.mark.asyncio
    async def test_get_rehearsal_not_found(self, client):
        response = await client.get("/rehearsals/99999")
        assert response.status_code == 404


class TestBookRehearsal:
    @pytest.mark.asyncio
    async def test_book_rehearsal_success(self, client, test_student, test_room):
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post("/rehearsals/", json={
            "room_id": test_room.id,
            "student_id": test_student.id,
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(hours=2)).isoformat(),
        })
        assert response.status_code == 201
        data = response.json()
        assert data["rehearsal"]["room_id"] == test_room.id
        assert data["message"] == "Репетиция успешно забронирована"

    @pytest.mark.asyncio
    async def test_book_rehearsal_no_auth(self, client, test_room, test_student):
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        response = await client.post("/rehearsals/", json={
            "room_id": test_room.id,
            "student_id": test_student.id,
            "start_time": (now + timedelta(hours=1)).isoformat(),
            "end_time": (now + timedelta(hours=2)).isoformat(),
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_book_rehearsal_invalid_data(self, client, test_student):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post("/rehearsals/", json={"room_id": None})
        assert response.status_code == 422
