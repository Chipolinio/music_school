"""
Unit-тесты сервиса отчётов.

Тестируются: get_lesson_count_by_teacher, get_user_attendance, get_peak_hours_report,
generate_csv, export_*_csv
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date

from src.services.report import (
    get_lesson_count_by_teacher,
    get_user_attendance,
    get_peak_hours_report,
    generate_csv,
    export_lesson_count_csv,
    export_attendance_csv,
    export_peak_hours_csv,
)
from src.services.exceptions import UserNotFoundError


class TestGetLessonCountByTeacher:
    """Тесты функции get_lesson_count_by_teacher."""

    @pytest.mark.asyncio
    async def test_get_lesson_count_success(self, mock_lesson_booking_repo, mock_user_repo, mock_teacher_model):
        """Тест успешного получения статистики."""
        # Arrange
        mock_lesson_booking_repo.get_lesson_count_by_teacher.return_value = [
            {"teacher_id": 2, "lesson_count": 5},
        ]
        mock_user_repo.get_by_id.return_value = mock_teacher_model

        start = date(2025, 1, 1)
        end = date(2025, 1, 31)

        # Act
        result = await get_lesson_count_by_teacher(mock_lesson_booking_repo, mock_user_repo, start, end)

        # Assert
        assert len(result) == 1
        assert result[0]["teacher_id"] == 2
        assert result[0]["teacher_name"] == "Петров Пётр"
        assert result[0]["lesson_count"] == 5

    @pytest.mark.asyncio
    async def test_get_lesson_count_unknown_teacher(self, mock_lesson_booking_repo, mock_user_repo):
        """Тест когда преподаватель не найден."""
        mock_lesson_booking_repo.get_lesson_count_by_teacher.return_value = [
            {"teacher_id": 999, "lesson_count": 3},
        ]
        mock_user_repo.get_by_id.return_value = None

        start = date(2025, 1, 1)
        end = date(2025, 1, 31)

        result = await get_lesson_count_by_teacher(mock_lesson_booking_repo, mock_user_repo, start, end)

        assert result[0]["teacher_name"] == "Неизвестно"

    @pytest.mark.asyncio
    async def test_get_lesson_count_empty(self, mock_lesson_booking_repo, mock_user_repo):
        """Тест пустого результата."""
        mock_lesson_booking_repo.get_lesson_count_by_teacher.return_value = []

        result = await get_lesson_count_by_teacher(
            mock_lesson_booking_repo, mock_user_repo,
            date(2025, 1, 1), date(2025, 1, 31),
        )

        assert result == []


class TestGetUserAttendance:
    """Тесты функции get_user_attendance."""

    @pytest.mark.asyncio
    async def test_get_attendance_success(self, mock_lesson_booking_repo, mock_user_repo, mock_user_model):
        """Тест успешного получения статистики посещаемости."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_lesson_booking_repo.get_user_attendance_stats.return_value = {
            "total_lessons": 10,
            "booked": 8,
            "attended": 5,
        }

        result = await get_user_attendance(
            mock_lesson_booking_repo, mock_user_repo,
            user_id=1, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
        )

        assert result["user_id"] == 1
        assert result["user_name"] == "Иванов Иван"
        assert result["total_lessons"] == 10
        assert result["booked"] == 8
        assert result["attended"] == 5

    @pytest.mark.asyncio
    async def test_get_attendance_user_not_found(self, mock_lesson_booking_repo, mock_user_repo):
        """Тест когда пользователь не найден."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await get_user_attendance(
                mock_lesson_booking_repo, mock_user_repo,
                user_id=999, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
            )


class TestGetPeakHoursReport:
    """Тесты функции get_peak_hours_report."""

    @pytest.mark.asyncio
    async def test_get_peak_hours(self, mock_lesson_booking_repo):
        """Тест получения популярных часов."""
        mock_lesson_booking_repo.get_peak_hours.return_value = [
            {"hour": 14, "slot_count": 10},
            {"hour": 15, "slot_count": 7},
        ]

        result = await get_peak_hours_report(
            mock_lesson_booking_repo,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
        )

        assert len(result) == 2
        assert result[0]["hour"] == 14
        assert result[0]["slot_count"] == 10

    @pytest.mark.asyncio
    async def test_get_peak_hours_empty(self, mock_lesson_booking_repo):
        """Тест пустого результата."""
        mock_lesson_booking_repo.get_peak_hours.return_value = []

        result = await get_peak_hours_report(
            mock_lesson_booking_repo,
            date(2025, 1, 1), date(2025, 1, 31),
        )

        assert result == []


class TestGenerateCsv:
    """Тесты функции generate_csv."""

    def test_generate_csv_from_list_of_dicts(self):
        """Тест генерации CSV из списка словарей."""
        data = [
            {"name": "Иван", "count": 5},
            {"name": "Пётр", "count": 3},
        ]

        result = generate_csv(data)

        assert "name,count" in result
        assert "Иван,5" in result
        assert "Пётр,3" in result

    def test_generate_csv_empty(self):
        """Тест генерации CSV из пустого списка."""
        result = generate_csv([])
        assert result == ""

    def test_generate_csv_single_row(self):
        """Тест CSV с одной строкой."""
        data = [{"a": 1, "b": 2}]
        result = generate_csv(data)
        assert "a,b" in result
        assert "1,2" in result


class TestExportLessonCountCsv:
    """Тесты функции export_lesson_count_csv."""

    @pytest.mark.asyncio
    async def test_export_lesson_count_csv(self, mock_lesson_booking_repo, mock_user_repo, mock_teacher_model):
        """Тест экспорта CSV по урокам преподавателей."""
        mock_lesson_booking_repo.get_lesson_count_by_teacher.return_value = [
            {"teacher_id": 2, "lesson_count": 5},
        ]
        mock_user_repo.get_by_id.return_value = mock_teacher_model

        result = await export_lesson_count_csv(
            mock_lesson_booking_repo, mock_user_repo,
            date(2025, 1, 1), date(2025, 1, 31),
        )

        assert "teacher_id" in result
        assert "teacher_name" in result
        assert "lesson_count" in result
        assert "Петров Пётр" in result


class TestExportAttendanceCsv:
    """Тесты функции export_attendance_csv."""

    @pytest.mark.asyncio
    async def test_export_attendance_csv(self, mock_lesson_booking_repo, mock_user_repo, mock_user_model):
        """Тест экспорта CSV по посещаемости."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_lesson_booking_repo.get_user_attendance_stats.return_value = {
            "total_lessons": 10,
            "booked": 8,
            "attended": 5,
        }

        result = await export_attendance_csv(
            mock_lesson_booking_repo, mock_user_repo,
            user_id=1, start_date=date(2025, 1, 1), end_date=date(2025, 1, 31),
        )

        assert "user_id" in result
        assert "total_lessons" in result
        assert "10" in result


class TestExportPeakHoursCsv:
    """Тесты функции export_peak_hours_csv."""

    @pytest.mark.asyncio
    async def test_export_peak_hours_csv(self, mock_lesson_booking_repo):
        """Тест экспорта CSV по популярным часам."""
        mock_lesson_booking_repo.get_peak_hours.return_value = [
            {"hour": 14, "slot_count": 10},
        ]

        result = await export_peak_hours_csv(
            mock_lesson_booking_repo,
            date(2025, 1, 1), date(2025, 1, 31),
        )

        assert "hour" in result
        assert "slot_count" in result
        assert "14" in result
