"""
Unit-тесты сервиса бронирования уроков.

Тестируются: book_lesson, get_booking_by_id, get_student_bookings, cancel_booking
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.services.booking import book_lesson, get_booking_by_id, get_student_bookings, cancel_booking
from src.schemas.LessonBooking import LessonCreate, LessonResponse
from src.schemas.User import UserRole
from src.models.LessonBooking import Status as BookingStatus
from src.models.Notification import MessageType
from src.services.exceptions import (
    UserNotFoundError,
    SlotNotFoundError,
    InvalidRoleError,
    CapacityExceededError,
    BookingConflictError,
    BookingNotFoundError,
)


class TestBookLesson:
    """Тесты функции book_lesson."""

    @pytest.mark.asyncio
    async def test_book_lesson_success(self, mock_lesson_booking_repo, mock_lesson_slot_repo,
                                         mock_user_repo, mock_notification_repo,
                                         lesson_create_data, mock_user_model, mock_slot_model):
        """Тест успешного бронирования."""
        # Arrange
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_lesson_slot_repo.get_by_id.return_value = mock_slot_model
        mock_lesson_booking_repo.count_bookings_for_slot.return_value = 0
        mock_lesson_booking_repo.get_student_active_bookings.return_value = []

        created_booking = MagicMock()
        created_booking.id = 1
        created_booking.slot_id = 1
        created_booking.student_id = 1
        created_booking.status = BookingStatus.BOOKED
        created_booking.booked_at = datetime.now(timezone.utc)
        mock_lesson_booking_repo.create_booking.return_value = created_booking

        # Act
        response = await book_lesson(
            mock_lesson_booking_repo, mock_lesson_slot_repo, mock_user_repo,
            mock_notification_repo, lesson_create_data,
            current_user_id=1, current_user_role=UserRole.STUDENT,
        )

        # Assert
        assert isinstance(response, LessonResponse)
        assert response.student_id == 1
        assert response.slot_id == 1
        mock_notification_repo.create_notification.assert_called_once()
        mock_notification_repo.session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_book_lesson_student_not_found(self, mock_lesson_booking_repo, mock_lesson_slot_repo,
                                                   mock_user_repo, mock_notification_repo, lesson_create_data):
        """Тест когда студент не найден."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await book_lesson(
                mock_lesson_booking_repo, mock_lesson_slot_repo, mock_user_repo,
                mock_notification_repo, lesson_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_book_lesson_student_cannot_book_other(self, mock_lesson_booking_repo, mock_lesson_slot_repo,
                                                           mock_user_repo, mock_notification_repo,
                                                           lesson_create_data, mock_user_model):
        """Тест: STUDENT не может записать другого."""
        mock_user_repo.get_by_id.return_value = mock_user_model

        other_lesson = LessonCreate(slot_id=1, student_id=99)
        with pytest.raises(InvalidRoleError) as exc_info:
            await book_lesson(
                mock_lesson_booking_repo, mock_lesson_slot_repo, mock_user_repo,
                mock_notification_repo, other_lesson,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

        assert "только себя" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_book_lesson_admin_can_book_for_other(self, mock_lesson_booking_repo, mock_lesson_slot_repo,
                                                          mock_user_repo, mock_notification_repo,
                                                          lesson_create_data, mock_user_model, mock_slot_model):
        """Тест: ADMIN может записать другого студента."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_lesson_slot_repo.get_by_id.return_value = mock_slot_model
        mock_lesson_booking_repo.count_bookings_for_slot.return_value = 0
        mock_lesson_booking_repo.get_student_active_bookings.return_value = []

        created_booking = MagicMock()
        created_booking.id = 1
        created_booking.slot_id = 1
        created_booking.student_id = 1
        created_booking.status = BookingStatus.BOOKED
        created_booking.booked_at = datetime.now(timezone.utc)
        mock_lesson_booking_repo.create_booking.return_value = created_booking

        # ADMIN — должно пройти
        response = await book_lesson(
            mock_lesson_booking_repo, mock_lesson_slot_repo, mock_user_repo,
            mock_notification_repo, lesson_create_data,
            current_user_id=999, current_user_role=UserRole.ADMIN,
        )
        assert response.student_id == 1

    @pytest.mark.asyncio
    async def test_book_lesson_slot_not_found(self, mock_lesson_booking_repo, mock_lesson_slot_repo,
                                                mock_user_repo, mock_notification_repo,
                                                lesson_create_data, mock_user_model):
        """Тест когда слот не найден."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_lesson_slot_repo.get_by_id.return_value = None

        with pytest.raises(SlotNotFoundError):
            await book_lesson(
                mock_lesson_booking_repo, mock_lesson_slot_repo, mock_user_repo,
                mock_notification_repo, lesson_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_book_lesson_capacity_exceeded(self, mock_lesson_booking_repo, mock_lesson_slot_repo,
                                                   mock_user_repo, mock_notification_repo,
                                                   lesson_create_data, mock_user_model, mock_slot_model):
        """Тест превышения вместимости."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_lesson_slot_repo.get_by_id.return_value = mock_slot_model
        mock_slot_model.max_participants = 1
        mock_lesson_booking_repo.count_bookings_for_slot.return_value = 1

        with pytest.raises(CapacityExceededError) as exc_info:
            await book_lesson(
                mock_lesson_booking_repo, mock_lesson_slot_repo, mock_user_repo,
                mock_notification_repo, lesson_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )

        assert exc_info.value.slot_id == 1
        assert exc_info.value.max_participants == 1

    @pytest.mark.asyncio
    async def test_book_lesson_time_conflict(self, mock_lesson_booking_repo, mock_lesson_slot_repo,
                                               mock_user_repo, mock_notification_repo,
                                               lesson_create_data, mock_user_model, mock_slot_model):
        """Тест конфликта времени у студента."""
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_lesson_slot_repo.get_by_id.return_value = mock_slot_model
        mock_lesson_booking_repo.count_bookings_for_slot.return_value = 0

        conflicting_booking = MagicMock()
        conflicting_booking.id = 10
        conflicting_booking.slot = MagicMock()
        now = datetime.now(timezone.utc)
        conflicting_booking.slot.start_time = now + timedelta(hours=1)
        conflicting_booking.slot.end_time = now + timedelta(hours=2)
        mock_lesson_booking_repo.get_student_active_bookings.return_value = [conflicting_booking]

        with pytest.raises(BookingConflictError):
            await book_lesson(
                mock_lesson_booking_repo, mock_lesson_slot_repo, mock_user_repo,
                mock_notification_repo, lesson_create_data,
                current_user_id=1, current_user_role=UserRole.STUDENT,
            )


class TestGetBookingById:
    """Тесты функции get_booking_by_id."""

    @pytest.mark.asyncio
    async def test_get_booking_success(self, mock_lesson_booking_repo, mock_booking_model):
        """Тест успешного получения брони."""
        mock_lesson_booking_repo.get_booking_with_slot.return_value = mock_booking_model

        response = await get_booking_by_id(mock_lesson_booking_repo, 1)

        assert isinstance(response, LessonResponse)
        assert response.id == 1
        assert response.student_id == 1

    @pytest.mark.asyncio
    async def test_get_booking_not_found(self, mock_lesson_booking_repo):
        """Тест когда бронь не найдена."""
        mock_lesson_booking_repo.get_booking_with_slot.return_value = None

        with pytest.raises(BookingNotFoundError):
            await get_booking_by_id(mock_lesson_booking_repo, 999)


class TestGetStudentBookings:
    """Тесты функции get_student_bookings."""

    @pytest.mark.asyncio
    async def test_get_student_bookings(self, mock_lesson_booking_repo, mock_booking_model):
        """Тест получения броней студента."""
        mock_lesson_booking_repo.get_student_bookings.return_value = [mock_booking_model]

        result = await get_student_bookings(mock_lesson_booking_repo, 1)

        assert len(result) == 1
        assert result[0].student_id == 1

    @pytest.mark.asyncio
    async def test_get_student_bookings_empty(self, mock_lesson_booking_repo):
        """Тест пустого списка броней."""
        mock_lesson_booking_repo.get_student_bookings.return_value = []

        result = await get_student_bookings(mock_lesson_booking_repo, 1)

        assert result == []


class TestCancelBooking:
    """Тесты функции cancel_booking."""

    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, mock_lesson_booking_repo, mock_notification_repo,
                                            mock_booking_model):
        """Тест успешной отмены брони."""
        mock_lesson_booking_repo.get_booking_with_slot.return_value = mock_booking_model

        await cancel_booking(
            mock_lesson_booking_repo, mock_notification_repo,
            booking_id=1, current_user_id=1, current_user_role=UserRole.STUDENT,
        )

        assert mock_booking_model.status == BookingStatus.FREE
        mock_lesson_booking_repo.session.commit.assert_called()
        mock_notification_repo.create_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_booking_not_found(self, mock_lesson_booking_repo, mock_notification_repo):
        """Тест отмены несуществующей брони."""
        mock_lesson_booking_repo.get_booking_with_slot.return_value = None

        with pytest.raises(BookingNotFoundError):
            await cancel_booking(
                mock_lesson_booking_repo, mock_notification_repo,
                booking_id=999, current_user_id=1, current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_cancel_booking_not_owner(self, mock_lesson_booking_repo, mock_notification_repo,
                                              mock_booking_model):
        """Тест: STUDENT не может отменить чужую бронь."""
        mock_booking_model.student_id = 1
        mock_lesson_booking_repo.get_booking_with_slot.return_value = mock_booking_model

        with pytest.raises(InvalidRoleError) as exc_info:
            await cancel_booking(
                mock_lesson_booking_repo, mock_notification_repo,
                booking_id=1, current_user_id=999, current_user_role=UserRole.STUDENT,
            )

        assert "только свою" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_cancel_booking_admin_can_cancel_any(self, mock_lesson_booking_repo, mock_notification_repo,
                                                         mock_booking_model):
        """Тест: ADMIN может отменить любую бронь."""
        mock_booking_model.student_id = 1
        mock_lesson_booking_repo.get_booking_with_slot.return_value = mock_booking_model

        await cancel_booking(
            mock_lesson_booking_repo, mock_notification_repo,
            booking_id=1, current_user_id=999, current_user_role=UserRole.ADMIN,
        )

        assert mock_booking_model.status == BookingStatus.FREE
