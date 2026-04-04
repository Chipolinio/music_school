"""
Integration-тесты для user endpoints.
GET /users/{id}, GET /users/, PATCH /users/{id}
POST /users/{id}/deactivate, POST /users/{id}/activate
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


class TestGetUser:
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, client, test_student):
        response = await client.get(f"/users/{test_student.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == test_student.phone
        assert data["role"] == "STUDENT"

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, client):
        response = await client.get("/users/99999")
        assert response.status_code == 404
        assert response.json()["error"] == "UserNotFoundError"


class TestGetAllUsers:
    @pytest.mark.asyncio
    async def test_get_all_users(self, client, test_student, test_teacher):
        response = await client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert data["total"] >= 2

    @pytest.mark.asyncio
    async def test_get_users_with_role_filter(self, client, test_student, test_teacher):
        response = await client.get("/users/?role=STUDENT")
        assert response.status_code == 200
        data = response.json()
        assert all(u["role"] == "STUDENT" for u in data["users"])

    @pytest.mark.asyncio
    async def test_get_users_pagination(self, client):
        response = await client.get("/users/?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) <= 1


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_update_user_full_name(self, client, test_student):
        # Авторизуемся как студент
        await client.post("/auth/login", json={
            "phone": test_student.phone,
            "password": "Password123",
        })
        response = await client.patch(
            f"/users/{test_student.id}",
            json={"full_name": "Новое Имя"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["full_name"] == "Новое Имя"

    @pytest.mark.asyncio
    async def test_update_user_unauthorized(self, client, test_student):
        response = await client.patch(
            f"/users/{test_student.id}",
            json={"full_name": "Новое Имя"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client, test_student):
        await client.post("/auth/login", json={
            "phone": test_student.phone,
            "password": "Password123",
        })
        response = await client.patch("/users/99999", json={"full_name": "Новое Имя"})
        assert response.status_code == 404
        assert response.json()["error"] == "UserNotFoundError"


class TestDeactivateUser:
    @pytest.mark.asyncio
    async def test_deactivate_by_admin(self, client, test_admin, test_student):
        await client.post("/auth/login", json={
            "phone": test_admin.phone, "password": "Password123",
        })
        response = await client.post(f"/users/{test_student.id}/deactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_active"] is False

    @pytest.mark.asyncio
    async def test_deactivate_non_admin_forbidden(self, client, test_student):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post(f"/users/{test_student.id}/deactivate")
        assert response.status_code == 403
        assert "ADMIN" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_deactivate_unauthorized(self, client, test_student):
        response = await client.post(f"/users/{test_student.id}/deactivate")
        assert response.status_code == 401


class TestActivateUser:
    @pytest.mark.asyncio
    async def test_activate_by_admin(self, client, test_admin, test_student):
        await client.post("/auth/login", json={
            "phone": test_admin.phone, "password": "Password123",
        })
        await client.post(f"/users/{test_student.id}/deactivate")
        response = await client.post(f"/users/{test_student.id}/activate")
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_activate_non_admin_forbidden(self, client, test_student):
        await client.post("/auth/login", json={
            "phone": test_student.phone, "password": "Password123",
        })
        response = await client.post(f"/users/{test_student.id}/activate")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_activate_unauthorized(self, client, test_student):
        response = await client.post(f"/users/{test_student.id}/activate")
        assert response.status_code == 401
