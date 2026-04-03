"""
Integration-тесты сервиса бронирования.

Тестируются с реальной БД: book_lesson, cancel_booking, capacity, conflicts
"""

import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.booking import book_lesson, cancel_booking, get_booking_by_id, get_student_bookings
from src.schemas.LessonBooking import LessonCreate
from src.schemas.User import UserRole
from src.models.LessonBooking import LessonBooking, Status as BookingStatus
from src.services.exceptions import (
    SlotNotFoundError,
    CapacityExceededError,
    BookingConflictError,
    BookingNotFoundError,
)
from src.repositories.LessonBookingRepository import LessonBookingRepository
from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.UserRepository import UserRepository
from src.repositories.NotificationRepository import NotificationRepository


class TestBookingIntegration:
    """Integration-тесты бронирования."""

    @pytest.mark.asyncio
    async def test_book_lesson_success(self, session, test_student, test_teacher,
                                         test_room, test_slot,
                                         lesson_booking_repo, lesson_slot_repo,
                                         user_repo, notification_repo):
        """Тест успешного бронирования урока."""
        booking_data = LessonCreate(
            slot_id=test_slot.id,
            student_id=test_student.id,
        )

        response = await book_lesson(
            lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
            booking_data,
            current_user_id=test_student.id,
            current_user_role=UserRole.STUDENT,
        )

        assert response.student_id == test_student.id
        assert response.slot_id == test_slot.id

        # Проверяем, что бронь в БД
        db_booking = await session.get(LessonBooking, response.id)
        assert db_booking is not None
        assert db_booking.status == BookingStatus.BOOKED

    @pytest.mark.asyncio
    async def test_book_lesson_slot_not_found(self, session, test_student,
                                                lesson_booking_repo, lesson_slot_repo,
                                                user_repo, notification_repo):
        """Тест бронирования на несуществующий слот."""
        booking_data = LessonCreate(
            slot_id=99999,
            student_id=test_student.id,
        )

        with pytest.raises(SlotNotFoundError):
            await book_lesson(
                lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
                booking_data,
                current_user_id=test_student.id,
                current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_book_lesson_capacity_exceeded(self, session, test_student, test_teacher,
                                                   test_room, lesson_booking_repo, lesson_slot_repo,
                                                   user_repo, notification_repo):
        """Тест превышения вместимости слота."""
        # Создаём слот с вместимостью 1
        now = datetime.now(timezone.utc)
        slot = await lesson_slot_repo.create_slot(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=10),
            end_time=now + timedelta(hours=11),
            max_participants=1,
        )
        await session.commit()
        await session.refresh(slot)

        # Записываем первого студента
        student1_data = await user_repo.create_user(
            phone="+79005001111", full_name="Студент 1",
            hashed_password="hash", role="STUDENT",
        )
        await session.commit()
        await session.refresh(student1_data)

        booking1 = LessonCreate(slot_id=slot.id, student_id=student1_data.id)
        await book_lesson(
            lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
            booking1,
            current_user_id=student1_data.id,
            current_user_role=UserRole.STUDENT,
        )

        # Второй студент — должен получить ошибку
        student2_data = await user_repo.create_user(
            phone="+79005002222", full_name="Студент 2",
            hashed_password="hash", role="STUDENT",
        )
        await session.commit()
        await session.refresh(student2_data)

        booking2 = LessonCreate(slot_id=slot.id, student_id=student2_data.id)

        with pytest.raises(CapacityExceededError) as exc_info:
            await book_lesson(
                lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
                booking2,
                current_user_id=student2_data.id,
                current_user_role=UserRole.STUDENT,
            )

        assert exc_info.value.max_participants == 1

    @pytest.mark.asyncio
    async def test_cancel_booking(self, session, test_student, test_teacher,
                                    test_room, test_slot,
                                    lesson_booking_repo, lesson_slot_repo,
                                    user_repo, notification_repo):
        """Тест отмены бронирования."""
        # Создаём бронь
        booking_data = LessonCreate(
            slot_id=test_slot.id,
            student_id=test_student.id,
        )
        booking_response = await book_lesson(
            lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
            booking_data,
            current_user_id=test_student.id,
            current_user_role=UserRole.STUDENT,
        )

        # Отменяем
        await cancel_booking(
            lesson_booking_repo, notification_repo,
            booking_id=booking_response.id,
            current_user_id=test_student.id,
            current_user_role=UserRole.STUDENT,
        )

        # Проверяем статус в БД
        db_booking = await session.get(LessonBooking, booking_response.id)
        assert db_booking.status == BookingStatus.FREE

    @pytest.mark.asyncio
    async def test_booking_conflict_same_student(self, session, test_student, test_teacher,
                                                   test_room, lesson_booking_repo, lesson_slot_repo,
                                                   user_repo, notification_repo):
        """Тест: студент не может записаться на два пересекающихся слота."""
        now = datetime.now(timezone.utc)

        # Два слота на одно время
        slot1 = await lesson_slot_repo.create_slot(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=20),
            end_time=now + timedelta(hours=21),
            max_participants=5,
        )

        slot2 = await lesson_slot_repo.create_slot(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=20),  # То же время
            end_time=now + timedelta(hours=21),
            max_participants=5,
        )
        await session.commit()
        await session.refresh(slot1)
        await session.refresh(slot2)

        # Записываем на первый слот
        booking1 = LessonCreate(slot_id=slot1.id, student_id=test_student.id)
        await book_lesson(
            lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
            booking1,
            current_user_id=test_student.id,
            current_user_role=UserRole.STUDENT,
        )

        # На второй — конфликт
        booking2 = LessonCreate(slot_id=slot2.id, student_id=test_student.id)

        with pytest.raises(BookingConflictError):
            await book_lesson(
                lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
                booking2,
                current_user_id=test_student.id,
                current_user_role=UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_get_student_bookings(self, session, test_student, test_teacher,
                                          test_room, test_slot,
                                          lesson_booking_repo, lesson_slot_repo,
                                          user_repo, notification_repo):
        """Тест получения всех броней студента."""
        booking_data = LessonCreate(
            slot_id=test_slot.id,
            student_id=test_student.id,
        )
        await book_lesson(
            lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
            booking_data,
            current_user_id=test_student.id,
            current_user_role=UserRole.STUDENT,
        )

        bookings = await get_student_bookings(lesson_booking_repo, test_student.id)

        assert len(bookings) == 1
        assert bookings[0].slot_id == test_slot.id

    @pytest.mark.asyncio
    async def test_get_booking_by_id(self, session, test_student, test_teacher,
                                       test_room, test_slot,
                                       lesson_booking_repo, lesson_slot_repo,
                                       user_repo, notification_repo):
        """Тест получения брони по ID."""
        booking_data = LessonCreate(
            slot_id=test_slot.id,
            student_id=test_student.id,
        )
        booking_resp = await book_lesson(
            lesson_booking_repo, lesson_slot_repo, user_repo, notification_repo,
            booking_data,
            current_user_id=test_student.id,
            current_user_role=UserRole.STUDENT,
        )

        result = await get_booking_by_id(lesson_booking_repo, booking_resp.id)

        assert result.id == booking_resp.id
        assert result.student_id == test_student.id
