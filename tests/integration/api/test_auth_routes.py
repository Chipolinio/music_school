"""
Integration-тесты для auth endpoints.
POST /auth/register, /login, /logout
GET /auth/me
POST /auth/verify-token
"""

import pytest
import httpx
from httpx import ASGITransport
import random

from src.main import create_app
from src.utils.security import create_token


def _unique_phone():
    return f"+7999{random.randint(1000000, 9999999)}"


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


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        phone = _unique_phone()
        response = await client.post("/auth/register", json={
            "phone": phone, "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "Пользователь успешно зарегистрирован"
        assert data["user"]["phone"] == phone
        assert data["user"]["role"] == "STUDENT"
        assert "jwt_token" in response.cookies

    @pytest.mark.asyncio
    async def test_register_duplicate_phone(self, client):
        phone = _unique_phone()
        await client.post("/auth/register", json={
            "phone": phone, "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        response = await client.post("/auth/register", json={
            "phone": phone, "full_name": "Петров Пётр", "password": "SecurePass456",
        })
        assert response.status_code == 400
        assert response.json()["error"] == "UserAlreadyExistsError"

    @pytest.mark.asyncio
    async def test_register_invalid_phone(self, client):
        response = await client.post("/auth/register", json={
            "phone": "invalid", "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client):
        response = await client.post("/auth/register", json={
            "phone": _unique_phone(), "full_name": "Иванов Иван", "password": "123",
        })
        assert response.status_code == 422


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        phone = _unique_phone()
        await client.post("/auth/register", json={
            "phone": phone, "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        response = await client.post("/auth/login", json={
            "phone": phone, "password": "SecurePass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Успешный вход"
        assert "jwt_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client):
        phone = _unique_phone()
        await client.post("/auth/register", json={
            "phone": phone, "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        response = await client.post("/auth/login", json={
            "phone": phone, "password": "WrongPassword",
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_user_not_found(self, client):
        response = await client.post("/auth/login", json={
            "phone": "+79990000000", "password": "SecurePass123",
        })
        assert response.status_code in (401, 404)


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_success(self, client):
        phone = _unique_phone()
        await client.post("/auth/register", json={
            "phone": phone, "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        response = await client.post("/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Успешный выход"

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client):
        response = await client.post("/auth/logout")
        assert response.status_code == 200


class TestMe:
    @pytest.mark.asyncio
    async def test_get_me_with_token(self, client):
        phone = _unique_phone()
        await client.post("/auth/register", json={
            "phone": phone, "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        response = await client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == phone
        assert data["full_name"] == "Иванов Иван"

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, client):
        response = await client.get("/auth/me")
        assert response.status_code == 401


class TestVerifyToken:
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, client):
        phone = _unique_phone()
        await client.post("/auth/register", json={
            "phone": phone, "full_name": "Иванов Иван", "password": "SecurePass123",
        })
        response = await client.post("/auth/verify-token")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert "user_id" in data["payload"]

    @pytest.mark.asyncio
    async def test_verify_no_token(self, client):
        response = await client.post("/auth/verify-token")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
