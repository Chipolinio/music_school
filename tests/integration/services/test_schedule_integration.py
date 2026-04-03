"""
Integration-тесты сервиса расписания.

Тестируются с реальной БД: create_slot (conflict checks), update_slot, delete_slot
"""

import pytest
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.services.schedule import create_slot, get_slot_by_id, update_slot, delete_slot
from src.schemas.LessonSlot import LessonSlotCreate, LessonSlotUpdate
from src.schemas.User import UserRole
from src.models.LessonSlot import LessonSlot
from src.services.exceptions import SlotConflictError, SlotNotFoundError
from src.repositories.LessonSlotRepository import LessonSlotRepository
from src.repositories.UserRepository import UserRepository
from src.repositories.RoomRepository import RoomRepository


class TestScheduleIntegration:
    """Integration-тесты расписания."""

    @pytest.mark.asyncio
    async def test_create_slot_success(self, session, test_teacher, test_room,
                                         lesson_slot_repo, user_repo, room_repo):
        """Тест успешного создания слота."""
        now = datetime.now(timezone.utc)
        slot_data = LessonSlotCreate(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=5),
            end_time=now + timedelta(hours=6),
            max_participants=3,
        )

        response = await create_slot(
            lesson_slot_repo, user_repo, room_repo,
            slot_data, UserRole.ADMIN,
        )

        assert response.teacher_id == test_teacher.id
        assert response.room_id == test_room.id

        # Проверяем в БД
        db_slot = await session.get(LessonSlot, response.id)
        assert db_slot is not None
        assert db_slot.teacher_id == test_teacher.id

    @pytest.mark.asyncio
    async def test_create_slot_teacher_conflict(self, session, test_teacher, test_room,
                                                  lesson_slot_repo, user_repo, room_repo):
        """Тест конфликта преподавателя при создании слота."""
        now = datetime.now(timezone.utc)

        # Первый слот
        slot1_data = LessonSlotCreate(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=6),
            end_time=now + timedelta(hours=7),
            max_participants=3,
        )
        await create_slot(lesson_slot_repo, user_repo, room_repo, slot1_data, UserRole.ADMIN)

        # Второй слот — тот же преподаватель, то же время
        slot2_data = LessonSlotCreate(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=6),  # То же время
            end_time=now + timedelta(hours=7),
            max_participants=3,
        )

        with pytest.raises(SlotConflictError) as exc_info:
            await create_slot(lesson_slot_repo, user_repo, room_repo, slot2_data, UserRole.ADMIN)

        assert "Преподаватель уже занят" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_slot_room_conflict(self, session, test_teacher, test_room,
                                               lesson_slot_repo, user_repo, room_repo):
        """Тест конфликта комнаты при создании слота."""
        now = datetime.now(timezone.utc)

        # Создаём второго преподавателя
        user_repo2 = UserRepository(session)
        teacher2 = await user_repo2.create_user(
            phone="+79006001111", full_name="Преподаватель 2",
            hashed_password="hash", role="TEACHER",
        )
        await session.commit()
        await session.refresh(teacher2)

        # Слот для первого преподавателя
        slot1_data = LessonSlotCreate(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=7),
            end_time=now + timedelta(hours=8),
            max_participants=3,
        )
        await create_slot(lesson_slot_repo, user_repo, room_repo, slot1_data, UserRole.ADMIN)

        # Слот для второго — та же комната, то же время
        slot2_data = LessonSlotCreate(
            teacher_id=teacher2.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=7),
            end_time=now + timedelta(hours=8),
            max_participants=3,
        )

        with pytest.raises(SlotConflictError) as exc_info:
            await create_slot(lesson_slot_repo, user_repo, room_repo, slot2_data, UserRole.ADMIN)

        assert "Комната уже занята" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_slot_success(self, session, test_teacher, test_room,
                                         lesson_slot_repo, user_repo, room_repo):
        """Тест успешного обновления слота."""
        now = datetime.now(timezone.utc)

        # Создаём слот
        slot_data = LessonSlotCreate(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=8),
            end_time=now + timedelta(hours=9),
            max_participants=3,
        )
        created = await create_slot(lesson_slot_repo, user_repo, room_repo, slot_data, UserRole.ADMIN)

        # Обновляем max_participants
        update_data = LessonSlotUpdate(max_participants=10)
        response = await update_slot(
            lesson_slot_repo, user_repo, room_repo,
            created.id, update_data, UserRole.ADMIN,
        )

        assert response.max_participants == 10

        db_slot = await session.get(LessonSlot, created.id)
        assert db_slot.max_participants == 10

    @pytest.mark.asyncio
    async def test_delete_slot(self, session, test_teacher, test_room,
                                 lesson_slot_repo, user_repo, room_repo):
        """Тест удаления слота."""
        now = datetime.now(timezone.utc)
        slot_data = LessonSlotCreate(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=9),
            end_time=now + timedelta(hours=10),
            max_participants=3,
        )
        created = await create_slot(lesson_slot_repo, user_repo, room_repo, slot_data, UserRole.ADMIN)

        # Удаляем
        await delete_slot(lesson_slot_repo, created.id, UserRole.ADMIN)

        # Проверяем что слот удалён
        with pytest.raises(SlotNotFoundError):
            await get_slot_by_id(lesson_slot_repo, created.id)

    @pytest.mark.asyncio
    async def test_get_slot_by_id(self, session, test_teacher, test_room,
                                    lesson_slot_repo, user_repo, room_repo):
        """Тест получения слота по ID."""
        now = datetime.now(timezone.utc)
        slot_data = LessonSlotCreate(
            teacher_id=test_teacher.id,
            room_id=test_room.id,
            start_time=now + timedelta(hours=11),
            end_time=now + timedelta(hours=12),
            max_participants=5,
        )
        created = await create_slot(lesson_slot_repo, user_repo, room_repo, slot_data, UserRole.ADMIN)

        response = await get_slot_by_id(lesson_slot_repo, created.id)

        assert response.id == created.id
        assert response.max_participants == 5
