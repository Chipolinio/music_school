"""
Integration-тесты для booking endpoints.
GET /bookings/{id}, GET /bookings/student/{id}
POST /bookings/, POST /bookings/{id}/cancel
"""

import pytest
import httpx
from httpx import ASGITransport

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


class TestGetBooking:
    @pytest.mark.asyncio
    async def test_get_booking_by_id(self, client, test_booking):
        response = await client.get(f"/bookings/{test_booking.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == test_booking.student_id
        assert data["slot_id"] == test_booking.slot_id

    @pytest.mark.asyncio
    async def test_get_booking_not_found(self, client):
        response = await client.get("/bookings/99999")
        assert response.status_code == 404


class TestGetStudentBookings:
    @pytest.mark.asyncio
    async def test_get_student_bookings(self, client, test_booking, test_student):
        response = await client.get(f"/bookings/student/{test_student.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_student_bookings_empty(self, client, test_student):
        response = await client.get(f"/bookings/student/{test_student.id}")
        assert response.status_code == 200
        assert response.json()["total"] == 0


class TestBookLesson:
    @pytest.mark.asyncio
    async def test_book_lesson_success(self, client, test_student, test_slot):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post("/bookings/", json={
            "slot_id": test_slot.id, "student_id": test_student.id,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["booking"]["slot_id"] == test_slot.id
        assert data["message"] == "Успешная запись на урок"

    @pytest.mark.asyncio
    async def test_book_lesson_no_auth(self, client, test_slot, test_student):
        response = await client.post("/bookings/", json={
            "slot_id": test_slot.id, "student_id": test_student.id,
        })
        assert response.status_code == 401


class TestCancelBooking:
    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, client, test_booking, test_student):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post(f"/bookings/{test_booking.id}/cancel")
        assert response.status_code == 200
        assert "отменена" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_booking_no_auth(self, client, test_booking):
        response = await client.post(f"/bookings/{test_booking.id}/cancel")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cancel_booking_not_found(self, client, test_student):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post("/bookings/99999/cancel")
        assert response.status_code == 404
