"""
Unit-тесты сервиса расписания.

Тестируются: create_slot, get_slot_by_id, get_all_slots, get_teacher_slots, update_slot, delete_slot
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

from src.services.schedule import (
    create_slot, get_slot_by_id, get_all_slots, get_teacher_slots, update_slot, delete_slot,
)
from src.schemas.LessonSlot import LessonSlotCreate, LessonSlotResponse, LessonSlotUpdate
from src.schemas.User import UserRole
from src.services.exceptions import (
    InvalidRoleError,
    UserNotFoundError,
    RoomNotFoundError,
    SlotNotFoundError,
    SlotConflictError,
)


class TestCreateSlot:
    """Тесты функции create_slot."""

    @pytest.mark.asyncio
    async def test_create_slot_success(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                        lesson_slot_create_data, mock_teacher_model, mock_room_model):
        """Тест успешного создания слота."""
        # Arrange
        mock_user_repo.get_by_id.return_value = mock_teacher_model
        mock_room_repo.get_by_id.return_value = mock_room_model
        mock_lesson_slot_repo.find_teacher_conflicts.return_value = []
        mock_lesson_slot_repo.find_conflicts.return_value = []

        created_slot = MagicMock()
        created_slot.id = 1
        created_slot.teacher_id = 2
        created_slot.room_id = 1
        created_slot.start_time = lesson_slot_create_data.start_time
        created_slot.end_time = lesson_slot_create_data.end_time
        created_slot.max_participants = 3
        mock_lesson_slot_repo.create_slot.return_value = created_slot

        # Act
        response = await create_slot(
            mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
            lesson_slot_create_data, UserRole.ADMIN,
        )

        # Assert
        assert isinstance(response, LessonSlotResponse)
        assert response.id == 1
        assert response.teacher_id == 2

    @pytest.mark.asyncio
    async def test_create_slot_non_admin_forbidden(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                                     lesson_slot_create_data):
        """Тест создания слота без прав ADMIN."""
        with pytest.raises(InvalidRoleError):
            await create_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                lesson_slot_create_data, UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_create_slot_teacher_not_found(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                                   lesson_slot_create_data, mock_room_model):
        """Тест когда преподаватель не найден."""
        mock_user_repo.get_by_id.return_value = None
        mock_room_repo.get_by_id.return_value = mock_room_model

        with pytest.raises(UserNotFoundError):
            await create_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                lesson_slot_create_data, UserRole.ADMIN,
            )

    @pytest.mark.asyncio
    async def test_create_slot_room_not_found(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                                lesson_slot_create_data, mock_teacher_model):
        """Тест когда комната не найдена."""
        mock_user_repo.get_by_id.return_value = mock_teacher_model
        mock_room_repo.get_by_id.return_value = None

        with pytest.raises(RoomNotFoundError):
            await create_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                lesson_slot_create_data, UserRole.ADMIN,
            )

    @pytest.mark.asyncio
    async def test_create_slot_teacher_conflict(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                                  lesson_slot_create_data, mock_teacher_model, mock_room_model):
        """Тест конфликта преподавателя."""
        mock_user_repo.get_by_id.return_value = mock_teacher_model
        mock_room_repo.get_by_id.return_value = mock_room_model
        mock_lesson_slot_repo.find_teacher_conflicts.return_value = [MagicMock()]

        with pytest.raises(SlotConflictError) as exc_info:
            await create_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                lesson_slot_create_data, UserRole.ADMIN,
            )

        assert "Преподаватель уже занят" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_slot_room_conflict(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                               lesson_slot_create_data, mock_teacher_model, mock_room_model):
        """Тест конфликта комнаты."""
        mock_user_repo.get_by_id.return_value = mock_teacher_model
        mock_room_repo.get_by_id.return_value = mock_room_model
        mock_lesson_slot_repo.find_teacher_conflicts.return_value = []
        mock_lesson_slot_repo.find_conflicts.return_value = [MagicMock()]

        with pytest.raises(SlotConflictError) as exc_info:
            await create_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                lesson_slot_create_data, UserRole.ADMIN,
            )

        assert "Комната уже занята" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_slot_too_short(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                           mock_teacher_model, mock_room_model):
        """Тест валидной длительности (1.5 часа — в пределах нормы)."""
        now = datetime.now(timezone.utc)
        valid_slot = LessonSlotCreate(
            teacher_id=2,
            room_id=1,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2, minutes=30),  # 1.5 часа — ок
            max_participants=1,
        )
        mock_user_repo.get_by_id.return_value = mock_teacher_model
        mock_room_repo.get_by_id.return_value = mock_room_model
        mock_lesson_slot_repo.find_teacher_conflicts.return_value = []
        mock_lesson_slot_repo.find_conflicts.return_value = []

        created_slot = MagicMock()
        created_slot.id = 1
        created_slot.teacher_id = 2
        created_slot.room_id = 1
        created_slot.start_time = valid_slot.start_time
        created_slot.end_time = valid_slot.end_time
        created_slot.max_participants = 1
        mock_lesson_slot_repo.create_slot.return_value = created_slot

        response = await create_slot(
            mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
            valid_slot, UserRole.ADMIN,
        )
        assert response is not None

    @pytest.mark.asyncio
    async def test_create_slot_too_short_validation(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                                      mock_teacher_model, mock_room_model):
        """Тест валидации: слот < 60 минут."""
        now = datetime.now(timezone.utc)
        too_short = LessonSlotCreate(
            teacher_id=2,
            room_id=1,
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=1, minutes=50),  # 50 минут — слишком мало для сервиса
            max_participants=1,
        )
        mock_user_repo.get_by_id.return_value = mock_teacher_model
        mock_room_repo.get_by_id.return_value = mock_room_model
        mock_lesson_slot_repo.find_teacher_conflicts.return_value = []
        mock_lesson_slot_repo.find_conflicts.return_value = []

        with pytest.raises(ValueError) as exc_info:
            await create_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                too_short, UserRole.ADMIN,
            )

        assert "Минимальная длительность" in str(exc_info.value)


class TestGetSlotById:
    """Тесты функции get_slot_by_id."""

    @pytest.mark.asyncio
    async def test_get_slot_success(self, mock_lesson_slot_repo, mock_slot_model):
        """Тест успешного получения слота."""
        mock_lesson_slot_repo.get_by_id.return_value = mock_slot_model

        response = await get_slot_by_id(mock_lesson_slot_repo, 1)

        assert isinstance(response, LessonSlotResponse)
        assert response.id == 1

    @pytest.mark.asyncio
    async def test_get_slot_not_found(self, mock_lesson_slot_repo):
        """Тест когда слот не найден."""
        mock_lesson_slot_repo.get_by_id.return_value = None

        with pytest.raises(SlotNotFoundError):
            await get_slot_by_id(mock_lesson_slot_repo, 999)


class TestGetAllSlots:
    """Тесты функции get_all_slots."""

    @pytest.mark.asyncio
    async def test_get_all_slots(self, mock_lesson_slot_repo, mock_slot_model):
        """Тест получения всех слотов."""
        mock_lesson_slot_repo.get_all.return_value = [mock_slot_model]

        result = await get_all_slots(mock_lesson_slot_repo)

        assert len(result) == 1
        assert result[0].id == 1


class TestGetTeacherSlots:
    """Тесты функции get_teacher_slots."""

    @pytest.mark.asyncio
    async def test_get_teacher_slots(self, mock_lesson_slot_repo, mock_slot_model):
        """Тест получения слотов преподавателя."""
        mock_lesson_slot_repo.get_by_teacher.return_value = [mock_slot_model]

        result = await get_teacher_slots(mock_lesson_slot_repo, 2)

        assert len(result) == 1
        assert result[0].teacher_id == 2


class TestUpdateSlot:
    """Тесты функции update_slot."""

    @pytest.mark.asyncio
    async def test_update_slot_success(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                                         mock_slot_model):
        """Тест успешного обновления слота."""
        mock_lesson_slot_repo.get_by_id.return_value = mock_slot_model
        mock_lesson_slot_repo.find_teacher_conflicts.return_value = []
        mock_lesson_slot_repo.find_conflicts.return_value = []

        updated_slot = MagicMock()
        updated_slot.id = 1
        updated_slot.teacher_id = 2
        updated_slot.room_id = 1
        now = datetime.now(timezone.utc)
        updated_slot.start_time = now + timedelta(hours=3)
        updated_slot.end_time = now + timedelta(hours=4)
        updated_slot.max_participants = 3
        mock_lesson_slot_repo.update.return_value = updated_slot

        update_data = LessonSlotUpdate(
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
        )

        response = await update_slot(
            mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
            1, update_data, UserRole.ADMIN,
        )

        assert isinstance(response, LessonSlotResponse)

    @pytest.mark.asyncio
    async def test_update_slot_non_admin_forbidden(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo):
        """Тест обновления без прав ADMIN."""
        update_data = LessonSlotUpdate()
        with pytest.raises(InvalidRoleError):
            await update_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                1, update_data, UserRole.STUDENT,
            )

    @pytest.mark.asyncio
    async def test_update_slot_not_found(self, mock_lesson_slot_repo, mock_user_repo, mock_room_repo):
        """Тест обновления несуществующего слота."""
        mock_lesson_slot_repo.get_by_id.return_value = None
        update_data = LessonSlotUpdate()

        with pytest.raises(SlotNotFoundError):
            await update_slot(
                mock_lesson_slot_repo, mock_user_repo, mock_room_repo,
                999, update_data, UserRole.ADMIN,
            )


class TestDeleteSlot:
    """Тесты функции delete_slot."""

    @pytest.mark.asyncio
    async def test_delete_slot_success(self, mock_lesson_slot_repo, mock_slot_model):
        """Тест успешного удаления."""
        mock_lesson_slot_repo.get_by_id.return_value = mock_slot_model

        await delete_slot(mock_lesson_slot_repo, 1, UserRole.ADMIN)

        mock_lesson_slot_repo.delete.assert_called_once()
        mock_lesson_slot_repo.session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_slot_non_admin_forbidden(self, mock_lesson_slot_repo):
        """Тест удаления без прав ADMIN."""
        with pytest.raises(InvalidRoleError):
            await delete_slot(mock_lesson_slot_repo, 1, UserRole.STUDENT)

    @pytest.mark.asyncio
    async def test_delete_slot_not_found(self, mock_lesson_slot_repo):
        """Тест удаления несуществующего слота."""
        mock_lesson_slot_repo.get_by_id.return_value = None

        with pytest.raises(SlotNotFoundError):
            await delete_slot(mock_lesson_slot_repo, 999, UserRole.ADMIN)
