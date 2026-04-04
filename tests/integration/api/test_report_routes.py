"""
Integration-тесты для report endpoints.
GET /reports/lessons-by-teacher, /reports/attendance/{id}, /reports/peak-hours
CSV-экспорты
"""

from datetime import date, timedelta

import pytest
import httpx
from httpx import ASGITransport

from src.main import create_app
from src.utils.security import create_token



def _date_params(days=7):
    today = date.today()
    return {
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=days)).isoformat(),
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


class TestLessonCountByTeacher:
    @pytest.mark.asyncio
    async def test_lesson_count_success(self, client, test_slot, test_booking):
        response = await client.get("/reports/lessons-by-teacher", params=_date_params())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_lesson_count_empty(self, client):
        response = await client.get("/reports/lessons-by-teacher", params={
            "start_date": "2020-01-01", "end_date": "2020-01-07",
        })
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_lesson_count_missing_params(self, client):
        response = await client.get("/reports/lessons-by-teacher")
        assert response.status_code == 422


class TestExportLessonCountCSV:
    @pytest.mark.asyncio
    async def test_export_csv(self, client, test_slot, test_booking):
        response = await client.get("/reports/lessons-by-teacher/csv", params=_date_params())
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert "lesson_count.csv" in response.headers.get("content-disposition", "")

    @pytest.mark.asyncio
    async def test_export_csv_missing_params(self, client):
        response = await client.get("/reports/lessons-by-teacher/csv")
        assert response.status_code == 422


class TestUserAttendance:
    @pytest.mark.asyncio
    async def test_attendance_success(self, client, test_student, test_booking):
        response = await client.get(
            f"/reports/attendance/{test_student.id}",
            params=_date_params(),
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_lessons" in data

    @pytest.mark.asyncio
    async def test_attendance_missing_params(self, client, test_student):
        response = await client.get(f"/reports/attendance/{test_student.id}")
        assert response.status_code == 422


class TestExportAttendanceCSV:
    @pytest.mark.asyncio
    async def test_export_csv(self, client, test_student, test_booking):
        response = await client.get(
            f"/reports/attendance/{test_student.id}/csv",
            params=_date_params(),
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert "attendance.csv" in response.headers.get("content-disposition", "")


class TestPeakHours:
    @pytest.mark.asyncio
    async def test_peak_hours_success(self, client, test_slot, test_booking):
        response = await client.get("/reports/peak-hours", params=_date_params())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_peak_hours_missing_params(self, client):
        response = await client.get("/reports/peak-hours")
        assert response.status_code == 422


class TestExportPeakHoursCSV:
    @pytest.mark.asyncio
    async def test_export_csv(self, client, test_slot, test_booking):
        response = await client.get("/reports/peak-hours/csv", params=_date_params())
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert "peak_hours.csv" in response.headers.get("content-disposition", "")
