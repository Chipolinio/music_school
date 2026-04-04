"""
Тесты для LessonBookingRepository.

Покрывает методы: create_booking, get_student_bookings, get_student_active_bookings,
count_bookings_for_slot, get_booking_with_slot, get_lesson_count_by_teacher,
get_user_attendance_stats, get_peak_hours.

Чеклист (раздел 5.5):
| Метод | Тест |
|-------|------|
| `create_booking` | Создание со статусом |
| `get_student_bookings` | Все брони студента |
| `get_student_active_bookings` | Только BOOKED (selectinload) |
| `count_bookings_for_slot` | Только BOOKED, игнор FREE/TAKEN |
| `get_booking_with_slot` | Eager loading slot |
| `get_lesson_count_by_teacher` | JOIN + GROUP BY |
| `get_user_attendance_stats` | JOIN + CASE + SUM |
| `get_peak_hours` | EXTRACT hour + GROUP BY + ORDER BY |
"""

import pytest
from datetime import datetime, timedelta, timezone, date

from src.models.User import User, UserRole
from src.models.Room import Room
from src.models.LessonSlot import LessonSlot
from src.models.LessonBooking import LessonBooking, Status
from src.repositories.LessonBookingRepository import LessonBookingRepository


class TestLessonBookingRepositoryCreateBooking:
    """Тесты метода create_booking."""

    @pytest.mark.asyncio
    async def test_create_booking(self, session, slot, student):
        """Тест создания бронирования."""
        repo = LessonBookingRepository(session)

        booking = await repo.create_booking(
            slot_id=slot.id,
            student_id=student.id,
            status="BOOKED",
        )

        assert booking.id is not None
        assert booking.slot_id == slot.id
        assert booking.student_id == student.id
        assert booking.status == Status.BOOKED

    @pytest.mark.asyncio
    async def test_create_booking_default_status(self, session, slot, student):
        """Тест: статус BOOKED по умолчанию."""
        repo = LessonBookingRepository(session)

        booking = await repo.create_booking(
            slot_id=slot.id,
            student_id=student.id,
        )

        assert booking.status == Status.BOOKED

    @pytest.mark.asyncio
    async def test_create_booking_free_status(self, session, slot, student):
        """Тест создания бронирования со статусом FREE."""
        repo = LessonBookingRepository(session)

        booking = await repo.create_booking(
            slot_id=slot.id,
            student_id=student.id,
            status="FREE",
        )

        assert booking.status == Status.FREE

    @pytest.mark.asyncio
    async def test_create_booking_taken_status(self, session, slot, student):
        """Тест создания бронирования со статусом TAKEN."""
        repo = LessonBookingRepository(session)

        booking = await repo.create_booking(
            slot_id=slot.id,
            student_id=student.id,
            status="TAKEN",
        )

        assert booking.status == Status.TAKEN

    @pytest.mark.asyncio
    async def test_create_booking_returns_instance(self, session, slot, student):
        """create_booking возвращает тот же экземпляр."""
        repo = LessonBookingRepository(session)

        booking = await repo.create_booking(
            slot_id=slot.id,
            student_id=student.id,
            status="BOOKED",
        )

        assert isinstance(booking, LessonBooking)
        assert booking.id is not None


class TestLessonBookingRepositoryGetStudentBookings:
    """Тесты метода get_student_bookings."""

    @pytest.mark.asyncio
    async def test_get_student_bookings(self, session, slot, student):
        """Тест получения всех броней студента."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        bookings = await repo.get_student_bookings(student.id)
        assert len(bookings) == 1
        assert bookings[0].student_id == student.id

    @pytest.mark.asyncio
    async def test_get_student_bookings_multiple(self, session, slot, student, teacher, room):
        """Тест: несколько броней студента."""
        repo = LessonBookingRepository(session)
        slot_repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot2 = await slot_repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")
        await repo.create_booking(slot_id=slot2.id, student_id=student.id, status="FREE")

        bookings = await repo.get_student_bookings(student.id)
        assert len(bookings) == 2

    @pytest.mark.asyncio
    async def test_get_student_bookings_empty(self, session, student):
        """Тест: у студента нет броней."""
        repo = LessonBookingRepository(session)

        bookings = await repo.get_student_bookings(student.id)
        assert len(bookings) == 0


class TestLessonBookingRepositoryGetStudentActiveBookings:
    """Тесты метода get_student_active_bookings."""

    @pytest.mark.asyncio
    async def test_get_student_active_bookings(self, session, slot, student):
        """Тест: только активные (BOOKED) брони."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")
        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="FREE")

        active = await repo.get_student_active_bookings(student.id)
        assert len(active) == 1
        assert active[0].status == Status.BOOKED

    @pytest.mark.asyncio
    async def test_get_student_active_bookings_all_free(self, session, slot, student):
        """Тест: все брони FREE — пустой результат."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="FREE")

        active = await repo.get_student_active_bookings(student.id)
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_get_student_active_bookings_empty(self, session, student):
        """Тест: у студента нет броней."""
        repo = LessonBookingRepository(session)

        active = await repo.get_student_active_bookings(student.id)
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_get_student_active_bookings_eager_slot(self, session, slot, student):
        """Тест: eager loading slot в активных бронях."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        active = await repo.get_student_active_bookings(student.id)
        assert len(active) == 1
        assert active[0].slot is not None


class TestLessonBookingRepositoryCountBookingsForSlot:
    """Тесты метода count_bookings_for_slot."""

    @pytest.mark.asyncio
    async def test_count_bookings_for_slot(self, session, slot, student):
        """Тест подсчёта броней для слота."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")
        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="FREE")

        count = await repo.count_bookings_for_slot(slot.id)
        assert count == 1  # Только BOOKED

    @pytest.mark.asyncio
    async def test_count_bookings_for_slot_all_booked(self, session, slot, student, teacher, room):
        """Тест: все брони BOOKED."""
        repo = LessonBookingRepository(session)
        user_repo = UserRepository(session)

        student2 = await user_repo.create_user(
            phone="+79991111112", full_name="Студент 2",
            hashed_password="h", role="STUDENT",
        )

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")
        await repo.create_booking(slot_id=slot.id, student_id=student2.id, status="BOOKED")

        count = await repo.count_bookings_for_slot(slot.id)
        assert count == 2

    @pytest.mark.asyncio
    async def test_count_bookings_for_slot_zero(self, session, slot):
        """Тест: нет броней для слота."""
        repo = LessonBookingRepository(session)

        count = await repo.count_bookings_for_slot(slot.id)
        assert count == 0

    @pytest.mark.asyncio
    async def test_count_bookings_for_slot_only_free(self, session, slot, student):
        """Тест: только FREE брони — 0."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="FREE")

        count = await repo.count_bookings_for_slot(slot.id)
        assert count == 0


class TestLessonBookingRepositoryGetBookingWithSlot:
    """Тесты метода get_booking_with_slot."""

    @pytest.mark.asyncio
    async def test_get_booking_with_slot(self, session, slot, student):
        """Тест: бронь с подгруженным слотом (eager loading)."""
        repo = LessonBookingRepository(session)

        booking = await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        result = await repo.get_booking_with_slot(booking.id)
        assert result is not None
        assert result.slot is not None
        assert result.slot.id == slot.id

    @pytest.mark.asyncio
    async def test_get_booking_with_slot_not_found(self, session):
        """Тест: несуществующая бронь."""
        repo = LessonBookingRepository(session)

        result = await repo.get_booking_with_slot(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_booking_with_slot_eager_loading(self, session, slot, student):
        """Проверка eager loading: slot должен быть подгружен."""
        repo = LessonBookingRepository(session)
        booking = await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        result = await repo.get_booking_with_slot(booking.id)

        assert result is not None
        assert result.slot is not None
        assert result.slot.id == slot.id
        assert result.slot.teacher_id == slot.teacher_id


class TestLessonBookingRepositoryGetLessonCountByTeacher:
    """Тесты метода get_lesson_count_by_teacher."""

    @pytest.mark.asyncio
    async def test_get_lesson_count_by_teacher(self, session, slot, student):
        """Тест: количество уроков по преподавателям."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        today = date.today()
        result = await repo.get_lesson_count_by_teacher(today, today + timedelta(days=1))

        assert len(result) >= 1
        teacher_ids = [r["teacher_id"] for r in result]
        assert slot.teacher_id in teacher_ids

    @pytest.mark.asyncio
    async def test_get_lesson_count_by_teacher_empty(self, session):
        """Тест: нет данных за период."""
        repo = LessonBookingRepository(session)

        today = date.today()
        result = await repo.get_lesson_count_by_teacher(today, today + timedelta(days=1))

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_lesson_count_by_teacher_structure(self, session, slot, student):
        """Тест: структура результата."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        today = date.today()
        result = await repo.get_lesson_count_by_teacher(today, today + timedelta(days=1))

        if result:
            assert "teacher_id" in result[0]
            assert "lesson_count" in result[0]


class TestLessonBookingRepositoryGetUserAttendanceStats:
    """Тесты метода get_user_attendance_stats."""

    @pytest.mark.asyncio
    async def test_get_user_attendance_stats(self, session, slot, student):
        """Тест: статистика посещаемости."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        today = date.today()
        stats = await repo.get_user_attendance_stats(student.id, today, today + timedelta(days=1))

        assert stats["total_lessons"] >= 1
        assert stats["booked"] >= 1

    @pytest.mark.asyncio
    async def test_get_user_attendance_stats_empty(self, session, student):
        """Тест: нет данных за период."""
        repo = LessonBookingRepository(session)

        today = date.today()
        stats = await repo.get_user_attendance_stats(student.id, today, today + timedelta(days=1))

        assert stats["total_lessons"] == 0
        assert stats["booked"] == 0
        assert stats["attended"] == 0

    @pytest.mark.asyncio
    async def test_get_user_attendance_stats_structure(self, session, slot, student):
        """Тест: структура результата."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        today = date.today()
        stats = await repo.get_user_attendance_stats(student.id, today, today + timedelta(days=1))

        assert "total_lessons" in stats
        assert "booked" in stats
        assert "attended" in stats
        assert isinstance(stats["total_lessons"], int)


class TestLessonBookingRepositoryGetPeakHours:
    """Тесты метода get_peak_hours."""

    @pytest.mark.asyncio
    async def test_get_peak_hours(self, session, slot, student):
        """Тест: популярные часы."""
        repo = LessonBookingRepository(session)

        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        today = date.today()
        result = await repo.get_peak_hours(today, today + timedelta(days=1))

        assert len(result) >= 1
        assert "hour" in result[0]
        assert "slot_count" in result[0]

    @pytest.mark.asyncio
    async def test_get_peak_hours_empty(self, session):
        """Тест: нет данных за период."""
        repo = LessonBookingRepository(session)

        today = date.today()
        result = await repo.get_peak_hours(today, today + timedelta(days=1))

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_peak_hours_structure(self, session, slot, student):
        """Проверка структуры результата get_peak_hours."""
        repo = LessonBookingRepository(session)
        await repo.create_booking(slot_id=slot.id, student_id=student.id, status="BOOKED")

        today = date.today()
        result = await repo.get_peak_hours(today, today + timedelta(days=1))

        assert isinstance(result, list)
        if result:
            assert "hour" in result[0]
            assert "slot_count" in result[0]
            assert isinstance(result[0]["hour"], int)
            assert isinstance(result[0]["slot_count"], int)


from src.repositories.UserRepository import UserRepository
from src.repositories.LessonSlotRepository import LessonSlotRepository
