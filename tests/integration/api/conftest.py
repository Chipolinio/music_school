"""
Conftest для интеграционных тестов API-слоя (роутеры).

"""

import pytest
import httpx
from httpx import ASGITransport
from datetime import datetime, timezone, timedelta
import random

from src.main import create_app
from src.core.database import get_session
from src.utils.security import create_token



def _unique_phone():
    """Генерирует уникальный номер телефона (только цифры)."""
    return f"+7999{random.randint(1000000, 9999999)}"


@pytest.fixture
async def app(session):
    """FastAPI приложение с переопределённой сессией."""
    _app = create_app()

    async def override_get_session():
        yield session

    _app.dependency_overrides[get_session] = override_get_session
    yield _app
    _app.dependency_overrides.clear()


@pytest.fixture
async def client(app):
    """HTTP-клиент без авторизации."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def student_client(app, test_student):
    """HTTP-клиент с ролью STUDENT."""
    token = create_token({"sub": str(test_student.id), "role": "STUDENT"})
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.cookies.set("jwt_token", token, domain="test")
        yield ac


@pytest.fixture
async def teacher_client(app, test_teacher):
    """HTTP-клиент с ролью TEACHER."""
    token = create_token({"sub": str(test_teacher.id), "role": "TEACHER"})
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.cookies.set("jwt_token", token, domain="test")
        yield ac


@pytest.fixture
async def admin_client(app, test_admin):
    """HTTP-клиент с ролью ADMIN."""
    token = create_token({"sub": str(test_admin.id), "role": "ADMIN"})
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.cookies.set("jwt_token", token, domain="test")
        yield ac
