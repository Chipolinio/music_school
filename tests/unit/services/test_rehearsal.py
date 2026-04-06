"""
Unit-тесты сервиса бронирования репетиций.

Тестируются: book_rehearsal, get_rehearsal_by_id, get_student_rehearsals, cancel_rehearsal
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from src.services.rehearsal import book_rehearsal, get_rehearsal_by_id, get_student_rehearsals, cancel_rehearsal
from src.schemas.RehearsalBooking import RehearsalCreate, RehearsalResponse
from src.schemas.User import UserRole
from src.models.RehearsalBooking import Status as BookingStatus
from src.services.exceptions import (
    UserNotFoundError,
    RoomNotFoundError,
    InvalidRoleError,
    BookingConflictError,
    BookingNotFoundError,
)


class TestBookRehearsal:
    """Тесты функции book_rehearsal."""

    @pytest.mark.asyncio
    async def test_book_rehearsal_success(self, mock_rehearsal_repo, mock_lesson_slot_repo,
                                            mock_room_repo, mock_user_repo, mock_notification_repo,
                                            rehearsal_create_data, mock_user_model):
        """Тест успешного бронирования репетиции."""
        # Arrange
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_room_repo.get_by_id.return_value = MagicMock()  # room exists

        mock_rehearsal_repo.find_room_conflicts.return_value = []
        mock_rehearsal_repo.find_student_conflicts.return_value = []
        mock_lesson_slot_repo.find_room_lesson_conflicts.return_value = []

        created_booking = MagicMock()
        created_booking.id = 1
        created_booking.student_id = 1
        created_booking.room_id = 1
        created_booking.status = BookingStatus.BOOKED
        now = datetime.now(timezone.utc)
        created_booking.start_time = now + timedelta(hours=1)
        created_booking.end_time = now + timedelta(hours=2)
        mock_rehearsal_repo.create_rehearsal.return_value = created_booking

        response = await book_rehearsal(
            mock_rehearsal_repo, mock_lesson_slot_repo, mock_room_repo,
            mock_user_repo, mock_notification_repo, rehearsal_create_data,
            current_user_id=1, current_user_role=UserRole.STUDENT,
        )

        # Assert
        assert isinstance(response, RehearsalResponse)
        assert response.student_id == 1
        assert response.room_id == 1

    @pytest.mark.asyncio
    async def test_book_rehearsal_student_not_found(self, mock_rehearsal_repo, mock_lesson_slot_repo,
                                                      mock_room_repo, mock_user_repo, mock_notification_repo,
                                                      rehearsal_create_data):
        """Тест когда студент не найден."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await book_rehearsal(
                mock_rehearsal_repo, mock_lesson_slot_repo, mock_room_repo,
                mock_user_repo, mock_notification_repo, rehearsal_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_book_rehearsal_room_not_found(self, mock_rehearsal_repo, mock_lesson_slot_repo,
                                                    mock_room_repo, mock_user_repo, mock_notification_repo,
                                                    rehearsal_create_data, mock_user_model):
        """Тест когда комната не найдена."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_room_repo.get_by_id.return_value = None

        with pytest.raises(RoomNotFoundError):
            await book_rehearsal(
                mock_rehearsal_repo, mock_lesson_slot_repo, mock_room_repo,
                mock_user_repo, mock_notification_repo, rehearsal_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_book_rehearsal_student_cannot_book_other(self, mock_rehearsal_repo, mock_lesson_slot_repo,
                                                              mock_room_repo, mock_user_repo, mock_notification_repo,
                                                              rehearsal_create_data, mock_user_model):
        """Тест: STUDENT не может бронировать для другого."""
        mock_user_repo.get_by_id.return_value = mock_user_model

        other_rehearsal = RehearsalCreate(
            student_id=99,
            room_id=1,
            start_time=rehearsal_create_data.start_time,
            end_time=rehearsal_create_data.end_time,
        )

        with pytest.raises(InvalidRoleError):
            await book_rehearsal(
                mock_rehearsal_repo, mock_lesson_slot_repo, mock_room_repo,
                mock_user_repo, mock_notification_repo, other_rehearsal,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_book_rehearsal_room_conflict(self, mock_rehearsal_repo, mock_lesson_slot_repo,
                                                  mock_room_repo, mock_user_repo, mock_notification_repo,
                                                  rehearsal_create_data, mock_user_model):
        """Тест конфликта комнаты."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_room_repo.get_by_id.return_value = MagicMock()
        mock_rehearsal_repo.find_room_conflicts.return_value = [MagicMock()]

        with pytest.raises(BookingConflictError):
            await book_rehearsal(
                mock_rehearsal_repo, mock_lesson_slot_repo, mock_room_repo,
                mock_user_repo, mock_notification_repo, rehearsal_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_book_rehearsal_student_conflict(self, mock_rehearsal_repo, mock_lesson_slot_repo,
                                                     mock_room_repo, mock_user_repo, mock_notification_repo,
                                                     rehearsal_create_data, mock_user_model):
        """Тест конфликта у студента."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_room_repo.get_by_id.return_value = MagicMock()
        mock_rehearsal_repo.find_room_conflicts.return_value = []
        mock_lesson_slot_repo.find_room_lesson_conflicts.return_value = []
        mock_rehearsal_repo.find_student_conflicts.return_value = [MagicMock()]

        with pytest.raises(BookingConflictError):
            await book_rehearsal(
                mock_rehearsal_repo, mock_lesson_slot_repo, mock_room_repo,
                mock_user_repo, mock_notification_repo, rehearsal_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )


class TestGetRehearsalById:
    """Тесты функции get_rehearsal_by_id."""

    @pytest.mark.asyncio
    async def test_get_rehearsal_success(self, mock_rehearsal_repo, mock_rehearsal_model):
        """Тест успешного получения репетиции."""
        mock_rehearsal_repo.get_by_id.return_value = mock_rehearsal_model

        response = await get_rehearsal_by_id(mock_rehearsal_repo, 1)

        assert isinstance(response, RehearsalResponse)
        assert response.id == 1
        assert response.student_id == 1

    @pytest.mark.asyncio
    async def test_get_rehearsal_not_found(self, mock_rehearsal_repo):
        """Тест когда репетиция не найдена."""
        mock_rehearsal_repo.get_by_id.return_value = None

        with pytest.raises(BookingNotFoundError):
            await get_rehearsal_by_id(mock_rehearsal_repo, 999)


class TestGetStudentRehearsals:
    """Тесты функции get_student_rehearsals."""

    @pytest.mark.asyncio
    async def test_get_student_rehearsals(self, mock_rehearsal_repo, mock_rehearsal_model):
        """Тест получения репетиций студента."""
        mock_rehearsal_repo.get_student_rehearsals.return_value = [mock_rehearsal_model]

        result = await get_student_rehearsals(mock_rehearsal_repo, 1)

        assert len(result) == 1
        assert result[0].student_id == 1

    @pytest.mark.asyncio
    async def test_get_student_rehearsals_empty(self, mock_rehearsal_repo):
        """Тест пустого списка репетиций."""
        mock_rehearsal_repo.get_student_rehearsals.return_value = []

        result = await get_student_rehearsals(mock_rehearsal_repo, 1)

        assert result == []


class TestCancelRehearsal:
    """Тесты функции cancel_rehearsal."""

    @pytest.mark.asyncio
    async def test_cancel_rehearsal_success(self, mock_rehearsal_repo, mock_notification_repo,
                                              mock_rehearsal_model):
        """Тест успешной отмены репетиции."""
        mock_rehearsal_repo.get_by_id.return_value = mock_rehearsal_model

        await cancel_rehearsal(
            mock_rehearsal_repo, mock_notification_repo,
            rehearsal_id=1, current_user_id=1, current_user_role=UserRole.STUDENT,
        )

        assert mock_rehearsal_model.status == BookingStatus.FREE
        mock_rehearsal_repo.session.commit.assert_called()
        mock_notification_repo.create_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_rehearsal_not_found(self, mock_rehearsal_repo, mock_notification_repo):
        """Тест отмены несуществующей репетиции."""
        mock_rehearsal_repo.get_by_id.return_value = None

        with pytest.raises(BookingNotFoundError):
            await cancel_rehearsal(
                mock_rehearsal_repo, mock_notification_repo,
                rehearsal_id=999, current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_cancel_rehearsal_not_owner(self, mock_rehearsal_repo, mock_notification_repo,
                                                mock_rehearsal_model):
        """Тест: STUDENT не может отменить чужую репетицию."""
        mock_rehearsal_model.student_id = 1
        mock_rehearsal_repo.get_by_id.return_value = mock_rehearsal_model

        with pytest.raises(InvalidRoleError):
            await cancel_rehearsal(
                mock_rehearsal_repo, mock_notification_repo,
                rehearsal_id=1, current_user_id=999, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_cancel_rehearsal_admin_can_cancel_any(self, mock_rehearsal_repo, mock_notification_repo,
                                                           mock_rehearsal_model):
        """Тест: ADMIN может отменить любую репетицию."""
        mock_rehearsal_model.student_id = 1
        mock_rehearsal_repo.get_by_id.return_value = mock_rehearsal_model

        await cancel_rehearsal(
            mock_rehearsal_repo, mock_notification_repo,
            rehearsal_id=1, current_user_id=999, current_user_role=UserRole.ADMIN,
        )

        assert mock_rehearsal_model.status == BookingStatus.FREE
