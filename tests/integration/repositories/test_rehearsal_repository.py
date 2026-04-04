"""
Тесты для RehearsalBookingRepository.

Покрывает методы: create_rehearsal, find_room_conflicts, find_student_conflicts,
get_student_rehearsals.

Чеклист (раздел 5.6):
| Метод | Тест |
|-------|------|
| `create_rehearsal` | Создание со статусом |
| `find_room_conflicts` | BOOKED конфликт / FREE нет конфликта |
| `find_student_conflicts` | Пересечение по студенту |
| `get_student_rehearsals` | Все репетиции |
"""

import pytest
from datetime import datetime, timedelta, timezone

from src.models.User import User, UserRole
from src.models.Room import Room
from src.models.RehearsalBooking import RehearsalBooking, Status
from src.repositories.RehearsalBookingRepository import RehearsalRepository


class TestRehearsalRepositoryCreateRehearsal:
    """Тесты метода create_rehearsal."""

    @pytest.mark.asyncio
    async def test_create_rehearsal(self, session, student, room):
        """Тест создания репетиции."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        booking = await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        assert booking.id is not None
        assert booking.student_id == student.id
        assert booking.room_id == room.id
        assert booking.status == Status.BOOKED

    @pytest.mark.asyncio
    async def test_create_rehearsal_default_status(self, session, student, room):
        """Тест: статус BOOKED по умолчанию (в репозитории)."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        booking = await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        assert booking.status == Status.BOOKED

    @pytest.mark.asyncio
    async def test_create_rehearsal_taken_status(self, session, student, room):
        """Тест создания репетиции со статусом TAKEN."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        booking = await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="TAKEN",
        )

        assert booking.status == Status.TAKEN

    @pytest.mark.asyncio
    async def test_create_rehearsal_returns_instance(self, session, student, room):
        """create_rehearsal возвращает тот же экземпляр."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        booking = await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        assert isinstance(booking, RehearsalBooking)
        assert booking.id is not None


class TestRehearsalRepositoryFindRoomConflicts:
    """Тесты метода find_room_conflicts."""

    @pytest.mark.asyncio
    async def test_find_room_conflicts(self, session, student, room):
        """Тест: конфликт комнаты — BOOKED."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        conflicts = await repo.find_room_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1, minutes=30),
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_find_room_conflicts_no_conflict_different_status(self, session, student, room):
        """Тест: нет конфликта, если статус не BOOKED."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="FREE",
        )

        conflicts = await repo.find_room_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1, minutes=30),
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_room_conflicts_no_conflict_different_time(self, session, student, room):
        """Тест: нет конфликта, другое время."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        conflicts = await repo.find_room_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_room_conflicts_empty_db(self, session, room):
        """Тест: пустая БД — нет конфликтов."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        conflicts = await repo.find_room_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_room_conflicts_exclude_booking_id(self, session, student, room):
        """Тест: exclude_booking_id исключает текущую бронь."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        booking = await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        conflicts = await repo.find_room_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            exclude_booking_id=booking.id,
        )
        assert len(conflicts) == 0


class TestRehearsalRepositoryFindStudentConflicts:
    """Тесты метода find_student_conflicts."""

    @pytest.mark.asyncio
    async def test_find_student_conflicts(self, session, student, room):
        """Тест: конфликт студента."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        conflicts = await repo.find_student_conflicts(
            student_id=student.id,
            start_time=now + timedelta(hours=1, minutes=30),
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_find_student_conflicts_no_conflict(self, session, student, room):
        """Тест: нет конфликта у студента."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        conflicts = await repo.find_student_conflicts(
            student_id=student.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_student_conflicts_no_conflict_free_status(self, session, student, room):
        """Тест: нет конфликта, если статус FREE."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="FREE",
        )

        conflicts = await repo.find_student_conflicts(
            student_id=student.id,
            start_time=now + timedelta(hours=1, minutes=30),
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_student_conflicts_exclude_booking_id(self, session, student, room):
        """Тест: exclude_booking_id исключает текущую бронь."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        booking = await repo.create_rehearsal(
            student_id=student.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        conflicts = await repo.find_student_conflicts(
            student_id=student.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            exclude_booking_id=booking.id,
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_student_conflicts_different_student(self, session, room):
        """Тест: другой студент — нет конфликта."""
        repo = RehearsalRepository(session)
        user_repo = UserRepository(session)
        now = datetime.now(timezone.utc)

        student1 = await user_repo.create_user(
            phone="+79991111111", full_name="Студент 1",
            hashed_password="h", role="STUDENT",
        )
        student2 = await user_repo.create_user(
            phone="+79991111112", full_name="Студент 2",
            hashed_password="h", role="STUDENT",
        )

        await repo.create_rehearsal(
            student_id=student1.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            status="BOOKED",
        )

        conflicts = await repo.find_student_conflicts(
            student_id=student2.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 0


class TestRehearsalRepositoryGetStudentRehearsals:
    """Тесты метода get_student_rehearsals."""

    @pytest.mark.asyncio
    async def test_get_student_rehearsals(self, session, student, room):
        """Тест получения всех репетиций студента."""
        repo = RehearsalRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_rehearsal(
            student_id=student.id, room_id=room.id,
            start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2),
        )
        await repo.create_rehearsal(
            student_id=student.id, room_id=room.id,
            start_time=now + timedelta(hours=3), end_time=now + timedelta(hours=4),
        )

        rehearsals = await repo.get_student_rehearsals(student.id)
        assert len(rehearsals) == 2

    @pytest.mark.asyncio
    async def test_get_student_rehearsals_empty(self, session, student):
        """Тест: у студента нет репетиций."""
        repo = RehearsalRepository(session)

        rehearsals = await repo.get_student_rehearsals(student.id)
        assert len(rehearsals) == 0

    @pytest.mark.asyncio
    async def test_get_student_rehearsals_different_students(self, session, room):
        """Тест: репетиции разных студентов не пересекаются."""
        repo = RehearsalRepository(session)
        user_repo = UserRepository(session)
        now = datetime.now(timezone.utc)

        student1 = await user_repo.create_user(
            phone="+79991111111", full_name="Студент 1",
            hashed_password="h", role="STUDENT",
        )
        student2 = await user_repo.create_user(
            phone="+79991111112", full_name="Студент 2",
            hashed_password="h", role="STUDENT",
        )

        await repo.create_rehearsal(
            student_id=student1.id, room_id=room.id,
            start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2),
        )
        await repo.create_rehearsal(
            student_id=student2.id, room_id=room.id,
            start_time=now + timedelta(hours=3), end_time=now + timedelta(hours=4),
        )

        rehearsals1 = await repo.get_student_rehearsals(student1.id)
        rehearsals2 = await repo.get_student_rehearsals(student2.id)

        assert len(rehearsals1) == 1
        assert len(rehearsals2) == 1
        assert rehearsals1[0].student_id == student1.id
        assert rehearsals2[0].student_id == student2.id


from src.repositories.UserRepository import UserRepository
