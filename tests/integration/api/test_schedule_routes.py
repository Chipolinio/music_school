"""
Integration-тесты для schedule endpoints.
GET /schedule/{id}, GET /schedule/, GET /schedule/teacher/{id}
POST /schedule/, PATCH /schedule/{id}, DELETE /schedule/{id}
"""

from datetime import datetime, timezone, timedelta

import pytest
import httpx
from httpx import ASGITransport

from src.main import create_app
from src.utils.security import create_token



def _slot_data(teacher, room, hours=1):
    now = datetime.now(timezone.utc)
    return {
        "teacher_id": teacher.id,
        "room_id": room.id,
        "start_time": (now + timedelta(hours=hours)).isoformat(),
        "end_time": (now + timedelta(hours=hours + 1)).isoformat(),
        "max_participants": 3,
    }


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
async def teacher_client(app, test_teacher):
    token = create_token({"sub": str(test_teacher.id), "role": "TEACHER"})
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.cookies.set("jwt_token", token, domain="test")
        yield ac


@pytest.fixture
async def admin_client(app, test_admin):
    token = create_token({"sub": str(test_admin.id), "role": "ADMIN"})
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.cookies.set("jwt_token", token, domain="test")
        yield ac


class TestGetSlot:
    @pytest.mark.asyncio
    async def test_get_slot_by_id(self, client, test_slot):
        response = await client.get(f"/schedule/{test_slot.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["teacher_id"] == test_slot.teacher_id

    @pytest.mark.asyncio
    async def test_get_slot_not_found(self, client):
        response = await client.get("/schedule/99999")
        assert response.status_code == 404


class TestGetAllSlots:
    @pytest.mark.asyncio
    async def test_get_all_slots(self, client, test_slot):
        response = await client.get("/schedule/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_slots_pagination(self, client):
        response = await client.get("/schedule/?limit=1")
        assert response.status_code == 200
        assert len(response.json()["slots"]) <= 1


class TestGetTeacherSlots:
    @pytest.mark.asyncio
    async def test_get_teacher_slots(self, client, test_slot, test_teacher):
        response = await client.get(f"/schedule/teacher/{test_teacher.id}")
        assert response.status_code == 200
        assert response.json()["total"] >= 1


class TestCreateSlot:
    @pytest.mark.asyncio
    async def test_create_slot_success(self, client, test_admin, test_teacher, test_room):
        await client.post("/auth/login", json={
            "phone": test_admin.phone, "password": "Password123",
        })
        response = await client.post("/schedule/", json=_slot_data(test_teacher, test_room))
        assert response.status_code == 201
        data = response.json()
        assert data["slot"]["teacher_id"] == test_teacher.id

    @pytest.mark.asyncio
    async def test_create_slot_non_admin_forbidden(self, client, test_student, test_teacher, test_room):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post("/schedule/", json=_slot_data(test_teacher, test_room))
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_slot_no_token(self, client, test_teacher, test_room):
        response = await client.post("/schedule/", json=_slot_data(test_teacher, test_room))
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_slot_invalid_data(self, client, test_admin):
        await client.post("/auth/login", json={
            "phone": test_admin.phone, "password": "Password123",
        })
        response = await client.post("/schedule/", json={})
        assert response.status_code == 422


class TestUpdateSlot:
    @pytest.mark.asyncio
    async def test_update_slot_success(self, client, test_admin, test_slot, test_room):
        await client.post("/auth/login", json={
            "phone": test_admin.phone, "password": "Password123",
        })
        now = datetime.now(timezone.utc)
        response = await client.patch(
            f"/schedule/{test_slot.id}",
            json={
                "start_time": (now + timedelta(hours=3)).isoformat(),
                "end_time": (now + timedelta(hours=4)).isoformat(),
                "room_id": test_room.id,
                "max_participants": 5,
            },
        )
        assert response.status_code == 200
        assert response.json()["slot"]["max_participants"] == 5

    @pytest.mark.asyncio
    async def test_update_slot_non_admin_forbidden(self, client, test_student, test_slot):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        now = datetime.now(timezone.utc)
        response = await client.patch(
            f"/schedule/{test_slot.id}",
            json={
                "start_time": (now + timedelta(hours=3)).isoformat(),
                "end_time": (now + timedelta(hours=4)).isoformat(),
            },
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_slot_not_found(self, client, test_admin):
        await client.post("/auth/login", json={
            "phone": test_admin.phone, "password": "Password123",
        })
        now = datetime.now(timezone.utc)
        response = await client.patch(
            "/schedule/99999",
            json={
                "start_time": (now + timedelta(hours=3)).isoformat(),
                "end_time": (now + timedelta(hours=4)).isoformat(),
            },
        )
        assert response.status_code == 404


class TestDeleteSlot:
    @pytest.mark.asyncio
    async def test_delete_slot_success(self, client, test_admin, test_slot):
        await client.post("/auth/login", json={
            "phone": test_admin.phone, "password": "Password123",
        })
        response = await client.delete(f"/schedule/{test_slot.id}")
        assert response.status_code == 200
        assert "удалён" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_slot_non_admin_forbidden(self, client, test_student, test_slot):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.delete(f"/schedule/{test_slot.id}")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_slot_no_token(self, client, test_slot):
        response = await client.delete(f"/schedule/{test_slot.id}")
        assert response.status_code == 401
