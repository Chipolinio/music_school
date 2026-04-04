"""
Integration-тесты для room endpoints.
GET /rooms/active, GET /rooms/{id}, GET /rooms/
POST /rooms/, PATCH /rooms/{id}, DELETE /rooms/{id}
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


class TestGetActiveRooms:
    @pytest.mark.asyncio
    async def test_get_active_rooms(self, client, test_room):
        response = await client.get("/rooms/active")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(r["is_active"] is True for r in data["rooms"])


class TestGetRoom:
    @pytest.mark.asyncio
    async def test_get_room_by_id(self, client, test_room):
        response = await client.get(f"/rooms/{test_room.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_room.name.title()  # name_validator делает .title()
        assert data["capacity"] == test_room.capacity

    @pytest.mark.asyncio
    async def test_get_room_not_found(self, client):
        response = await client.get("/rooms/99999")
        assert response.status_code == 404
        assert response.json()["error"] == "RoomNotFoundError"


class TestGetAllRooms:
    @pytest.mark.asyncio
    async def test_get_all_rooms(self, client, test_room):
        response = await client.get("/rooms/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_get_rooms_pagination(self, client):
        response = await client.get("/rooms/?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["rooms"]) <= 1


class TestCreateRoom:
    @pytest.mark.asyncio
    async def test_create_room_success(self, client):
        response = await client.post("/rooms/", json={
            "name": "Класс фортепиано", "capacity": 3, "is_active": True,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["room"]["name"] == "Класс Фортепиано"  # name_validator делает .title()
        assert data["message"] == "Комната успешно создана"

    @pytest.mark.asyncio
    async def test_create_room_invalid_name(self, client):
        response = await client.post("/rooms/", json={
            "name": "1", "capacity": 3,
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_room_invalid_capacity(self, client):
        response = await client.post("/rooms/", json={
            "name": "Класс", "capacity": 0,
        })
        assert response.status_code == 422


class TestUpdateRoom:
    @pytest.mark.asyncio
    async def test_update_room_name(self, client, test_room):
        response = await client.patch(f"/rooms/{test_room.id}", json={"name": "Новое название"})
        assert response.status_code == 200
        data = response.json()
        assert data["room"]["name"] == "Новое Название"

    @pytest.mark.asyncio
    async def test_update_room_not_found(self, client):
        response = await client.patch("/rooms/99999", json={"name": "Новое"})
        assert response.status_code == 404


class TestDeleteRoom:
    @pytest.mark.asyncio
    async def test_delete_room_success(self, client, test_room):
        response = await client.delete(f"/rooms/{test_room.id}")
        assert response.status_code == 200
        assert "удалена" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_delete_room_not_found_after(self, client, test_room):
        await client.delete(f"/rooms/{test_room.id}")
        resp = await client.get(f"/rooms/{test_room.id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_room_not_found(self, client):
        response = await client.delete("/rooms/99999")
        assert response.status_code == 404
