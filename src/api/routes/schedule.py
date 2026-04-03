"""
API роуты для расписания уроков.
"""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_schedule_service, ScheduleService, get_current_user_from_request, require_admin
from src.schemas.User import UserRole
from src.schemas.LessonSlot import LessonSlotResponse, LessonSlotCreate, LessonSlotUpdate, LessonSlotListResponse, LessonSlotCreateResponse, LessonSlotUpdateResponse, LessonSlotDeleteResponse


router = APIRouter(prefix="/schedule", tags=["Расписание"])


@router.get("/{slot_id}", response_model=LessonSlotResponse)
async def get_slot(
    slot_id: int,
    service: ScheduleService = Depends(get_schedule_service),
):
    """Получение слота по ID."""
    return await service.get_by_id(slot_id)


@router.get("/", response_model=LessonSlotListResponse)
async def get_slots(
    skip: int = 0,
    limit: int = 100,
    service: ScheduleService = Depends(get_schedule_service),
):
    """Получение всех слотов с пагинацией."""
    slots = await service.get_all(skip=skip, limit=limit)
    return LessonSlotListResponse(slots=slots, total=len(slots))


@router.get("/teacher/{teacher_id}", response_model=LessonSlotListResponse)
async def get_teacher_slots(
    teacher_id: int,
    service: ScheduleService = Depends(get_schedule_service),
):
    """Получение всех слотов преподавателя."""
    slots = await service.get_teacher(teacher_id)
    return LessonSlotListResponse(slots=slots, total=len(slots))


@router.post("/", response_model=LessonSlotCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_slot(
    slot_data: LessonSlotCreate,
    user_data: dict = Depends(require_admin),
    service: ScheduleService = Depends(get_schedule_service),
):
    """Создание слота урока (только ADMIN)."""
    current_role = UserRole(user_data["role"])
    slot = await service.create(slot_data, current_role)
    return LessonSlotCreateResponse(slot=slot, message="Слот успешно создан")


@router.patch("/{slot_id}", response_model=LessonSlotUpdateResponse)
async def update_slot(
    slot_id: int,
    update_data: LessonSlotUpdate,
    user_data: dict = Depends(require_admin),
    service: ScheduleService = Depends(get_schedule_service),
):
    """Обновление слота (только ADMIN)."""
    current_role = UserRole(user_data["role"])
    slot = await service.update(slot_id, update_data, current_role)
    return LessonSlotUpdateResponse(slot=slot, message="Слот успешно обновлён")


@router.delete("/{slot_id}", response_model=LessonSlotDeleteResponse)
async def delete_slot(
    slot_id: int,
    user_data: dict = Depends(require_admin),
    service: ScheduleService = Depends(get_schedule_service),
):
    """Удаление слота (только ADMIN)."""
    current_role = UserRole(user_data["role"])
    await service.delete(slot_id, current_role)
    return LessonSlotDeleteResponse(message="Слот успешно удалён")
