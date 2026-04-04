"""
Тесты для LessonSlotRepository.

Покрывает методы: create_slot, find_conflicts, find_teacher_conflicts,
get_by_teacher, get_for_period, find_room_lesson_conflicts, get_slot_with_bookings.

Чеклист (раздел 5.4):
| Метод | Тест |
|-------|------|
| `create_slot` | Создание с LessonType |
| `find_conflicts` | Нет конфликта / Есть конфликт / exclude_slot_id |
| `find_teacher_conflicts` | Нет конфликта / Есть конфликт / exclude_slot_id |
| `get_by_teacher` | Слоты преподавателя |
| `get_for_period` | Один день / Период |
| `find_room_lesson_conflicts` | Пересечение интервалов |
| `get_slot_with_bookings` | Eager loading lesson_bookings |
"""

import pytest
from datetime import datetime, timedelta, timezone, date

from src.models.User import User, UserRole
from src.models.Room import Room
from src.models.LessonSlot import LessonSlot, LessonType
from src.models.LessonBooking import LessonBooking, Status
from src.repositories.LessonSlotRepository import LessonSlotRepository


class TestLessonSlotRepositoryCreateSlot:
    """Тесты метода create_slot."""

    @pytest.mark.asyncio
    async def test_create_slot(self, session, teacher, room):
        """Тест создания слота."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            max_participants=3,
            lesson_type="LESSON",
        )

        assert slot.id is not None
        assert slot.teacher_id == teacher.id
        assert slot.room_id == room.id
        assert slot.lesson_type == LessonType.LESSON

    @pytest.mark.asyncio
    async def test_create_slot_trial_lesson(self, session, teacher, room):
        """Тест создания слота с lesson_type=TRIAL."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            max_participants=1,
            lesson_type="TRIAL",
        )

        assert slot.lesson_type == LessonType.TRIAL

    @pytest.mark.asyncio
    async def test_create_slot_default_lesson_type(self, session, teacher, room):
        """Тест: lesson_type=LESSON по умолчанию."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        assert slot.lesson_type == LessonType.LESSON

    @pytest.mark.asyncio
    async def test_create_slot_returns_instance(self, session, teacher, room):
        """create_slot возвращает тот же экземпляр с заполненным ID."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        assert slot.id is not None
        assert isinstance(slot, LessonSlot)


class TestLessonSlotRepositoryFindConflicts:
    """Тесты метода find_conflicts."""

    @pytest.mark.asyncio
    async def test_find_conflicts_no_conflict(self, session, teacher, room):
        """Тест: нет конфликтов — пустой список."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_conflicts_has_conflict(self, session, teacher, room):
        """Тест: есть конфликт — слот найден."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1, minutes=30),
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_find_conflicts_exclude_slot_id(self, session, teacher, room):
        """Тест: exclude_slot_id исключает текущий слот."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            exclude_slot_id=slot.id,
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_conflicts_empty_db(self, session, room):
        """Тест: пустая БД — нет конфликтов."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_conflicts_full_overlap(self, session, teacher, room):
        """Тест: полное совпадение времени — конфликт."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_find_conflicts_partial_overlap_left(self, session, teacher, room):
        """Тест: частичное пересечение слева."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(minutes=30),
            end_time=now + timedelta(minutes=90),
        )
        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_find_conflicts_no_overlap_before(self, session, teacher, room):
        """Тест: слот до — нет конфликта."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=3),
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=0),
            end_time=now + timedelta(hours=1),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_conflicts_no_overlap_after(self, session, teacher, room):
        """Тест: слот после — нет конфликта."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_conflicts_different_room(self, session, teacher, room):
        """Тест: другая комната — нет конфликта."""
        repo = LessonSlotRepository(session)
        room_repo = RoomRepository(session)
        now = datetime.now(timezone.utc)

        room2 = await room_repo.create_room(name="Комната 2", capacity=3, is_active=True)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_conflicts(
            room_id=room2.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 0

    @pytest.mark.parametrize(
        "offset_start,offset_end,expected_conflicts",
        [
            (30, 90, True),     # Частичное пересечение справа
            (-30, 150, True),   # Полное покрытие
            (50, 90, True),     # Частичное пересечение слева
            (120, 180, False),  # После — нет конфликта
            (-120, -60, False), # До — нет конфликта
        ],
    )
    @pytest.mark.asyncio
    async def test_find_conflicts_all_scenarios(
        self, session, teacher, room, offset_start, offset_end, expected_conflicts
    ):
        """Параметризованный тест всех сценариев пересечения."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),    # 60 мин
            end_time=now + timedelta(hours=2),      # 120 мин
        )

        conflicts = await repo.find_conflicts(
            room_id=room.id,
            start_time=now + timedelta(minutes=offset_start),
            end_time=now + timedelta(minutes=offset_end),
        )

        has_conflicts = len(conflicts) > 0
        assert has_conflicts == expected_conflicts


class TestLessonSlotRepositoryFindTeacherConflicts:
    """Тесты метода find_teacher_conflicts."""

    @pytest.mark.asyncio
    async def test_find_teacher_conflicts_has_conflict(self, session, teacher, room):
        """Тест: есть конфликт у преподавателя."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_teacher_conflicts(
            teacher_id=teacher.id,
            start_time=now + timedelta(hours=1, minutes=30),
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_find_teacher_conflicts_no_conflict(self, session, teacher, room):
        """Тест: нет конфликта у преподавателя."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_teacher_conflicts(
            teacher_id=teacher.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_teacher_conflicts_exclude_slot_id(self, session, teacher, room):
        """Тест: exclude_slot_id исключает текущий слот."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_teacher_conflicts(
            teacher_id=teacher.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            exclude_slot_id=slot.id,
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_teacher_conflicts_empty_db(self, session, teacher):
        """Тест: пустая БД — нет конфликтов."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        conflicts = await repo.find_teacher_conflicts(
            teacher_id=teacher.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_teacher_conflicts_different_teacher(self, session, room):
        """Тест: другой преподаватель — нет конфликта."""
        repo = LessonSlotRepository(session)
        user_repo = UserRepository(session)
        now = datetime.now(timezone.utc)

        teacher1 = await user_repo.create_user(
            phone="+79992222222", full_name="Преподаватель 1",
            hashed_password="h", role="TEACHER",
        )
        teacher2 = await user_repo.create_user(
            phone="+79992222223", full_name="Преподаватель 2",
            hashed_password="h", role="TEACHER",
        )

        await repo.create_slot(
            teacher_id=teacher1.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_teacher_conflicts(
            teacher_id=teacher2.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 0


class TestLessonSlotRepositoryGetByTeacher:
    """Тесты метода get_by_teacher."""

    @pytest.mark.asyncio
    async def test_get_by_teacher(self, session, teacher, room):
        """Тест получения слотов преподавателя."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id, room_id=room.id,
            start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2),
        )
        await repo.create_slot(
            teacher_id=teacher.id, room_id=room.id,
            start_time=now + timedelta(hours=3), end_time=now + timedelta(hours=4),
        )

        slots = await repo.get_by_teacher(teacher.id)
        assert len(slots) == 2

    @pytest.mark.asyncio
    async def test_get_by_teacher_empty(self, session, teacher):
        """Тест: у преподавателя нет слотов."""
        repo = LessonSlotRepository(session)

        slots = await repo.get_by_teacher(teacher.id)
        assert len(slots) == 0

    @pytest.mark.asyncio
    async def test_get_by_teacher_different_teachers(self, session, room):
        """Тест: слоты разных преподавателей не пересекаются."""
        repo = LessonSlotRepository(session)
        user_repo = UserRepository(session)
        now = datetime.now(timezone.utc)

        teacher1 = await user_repo.create_user(
            phone="+79992222222", full_name="Преподаватель 1",
            hashed_password="h", role="TEACHER",
        )
        teacher2 = await user_repo.create_user(
            phone="+79992222223", full_name="Преподаватель 2",
            hashed_password="h", role="TEACHER",
        )

        await repo.create_slot(
            teacher_id=teacher1.id, room_id=room.id,
            start_time=now + timedelta(hours=1), end_time=now + timedelta(hours=2),
        )
        await repo.create_slot(
            teacher_id=teacher2.id, room_id=room.id,
            start_time=now + timedelta(hours=3), end_time=now + timedelta(hours=4),
        )

        slots1 = await repo.get_by_teacher(teacher1.id)
        slots2 = await repo.get_by_teacher(teacher2.id)

        assert len(slots1) == 1
        assert len(slots2) == 1
        assert slots1[0].teacher_id == teacher1.id
        assert slots2[0].teacher_id == teacher2.id


class TestLessonSlotRepositoryGetForPeriod:
    """Тесты метода get_for_period."""

    @pytest.mark.asyncio
    async def test_get_for_period_single_day(self, session, teacher, room):
        """Тест: слоты за один день."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)
        today = now.date()

        await repo.create_slot(
            teacher_id=teacher.id, room_id=room.id,
            start_time=now.replace(hour=10, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=11, minute=0, second=0, microsecond=0),
        )

        slots = await repo.get_for_period(start_date=today)
        assert len(slots) == 1

    @pytest.mark.asyncio
    async def test_get_for_period_empty(self, session, teacher, room):
        """Тест: нет слотов за период."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id, room_id=room.id,
            start_time=now + timedelta(days=10),
            end_time=now + timedelta(days=10, hours=1),
        )

        slots = await repo.get_for_period(start_date=now.date())
        assert len(slots) == 0


class TestLessonSlotRepositoryFindRoomLessonConflicts:
    """Тесты метода find_room_lesson_conflicts."""

    @pytest.mark.asyncio
    async def test_find_room_lesson_conflicts_has_conflict(self, session, teacher, room):
        """Тест: есть конфликт комнаты."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_room_lesson_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1, minutes=30),
            end_time=now + timedelta(hours=2, minutes=30),
        )
        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_find_room_lesson_conflicts_no_conflict(self, session, teacher, room):
        """Тест: нет конфликта комнаты."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        await repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        conflicts = await repo.find_room_lesson_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )
        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_find_room_lesson_conflicts_empty_db(self, session, room):
        """Тест: пустая БД — нет конфликтов."""
        repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        conflicts = await repo.find_room_lesson_conflicts(
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )
        assert len(conflicts) == 0


class TestLessonSlotRepositoryGetSlotWithBookings:
    """Тесты метода get_slot_with_bookings."""

    @pytest.mark.asyncio
    async def test_get_slot_with_bookings(self, session, teacher, room):
        """Тест: слот с подгруженными бронированиями."""
        slot_repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await slot_repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            max_participants=3,
        )

        booking = LessonBooking(
            slot_id=slot.id,
            student_id=teacher.id,
            status=Status.BOOKED,
        )
        session.add(booking)
        await session.flush()

        result = await slot_repo.get_slot_with_bookings(slot.id)
        assert result is not None
        assert len(result.lesson_bookings) == 1

    @pytest.mark.asyncio
    async def test_get_slot_with_bookings_no_bookings(self, session, teacher, room):
        """Тест: слот без бронирований — пустой список."""
        slot_repo = LessonSlotRepository(session)
        now = datetime.now(timezone.utc)

        slot = await slot_repo.create_slot(
            teacher_id=teacher.id,
            room_id=room.id,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
        )

        result = await slot_repo.get_slot_with_bookings(slot.id)
        assert result is not None
        assert len(result.lesson_bookings) == 0

    @pytest.mark.asyncio
    async def test_get_slot_with_bookings_not_found(self, session):
        """Тест: несуществующий слот."""
        slot_repo = LessonSlotRepository(session)
        result = await slot_repo.get_slot_with_bookings(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_slot_with_bookings_eager_loading(self, session, teacher, room, booking):
        """Проверка eager loading: slot должен быть подгружен."""
        slot_repo = LessonSlotRepository(session)
        booking_repo = LessonSlotRepository(session)

        slot = await slot_repo.get_slot_with_bookings(booking.slot_id)
        assert slot is not None
        assert slot.lesson_bookings is not None
        assert len(slot.lesson_bookings) >= 1


from src.repositories.UserRepository import UserRepository
from src.repositories.RoomRepository import RoomRepository
