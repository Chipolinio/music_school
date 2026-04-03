"""
API роуты для репетиций.
"""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_rehearsal_service, RehearsalService, get_current_user_from_request
from src.schemas.User import UserRole
from src.schemas.RehearsalBooking import RehearsalResponse, RehearsalCreate, RehearsalListResponse, RehearsalCreateResponse, RehearsalCancelResponse


router = APIRouter(prefix="/rehearsals", tags=["Репетиции"])


@router.get("/{rehearsal_id}", response_model=RehearsalResponse)
async def get_rehearsal(
    rehearsal_id: int,
    service: RehearsalService = Depends(get_rehearsal_service),
):
    """Получение репетиции по ID."""
    return await service.get_by_id(rehearsal_id)


@router.get("/student/{student_id}", response_model=RehearsalListResponse)
async def get_student_rehearsals(
    student_id: int,
    service: RehearsalService = Depends(get_rehearsal_service),
):
    """Получение всех репетиций студента."""
    rehearsals = await service.get_student(student_id)
    return RehearsalListResponse(rehearsals=rehearsals, total=len(rehearsals))


@router.post("/", response_model=RehearsalCreateResponse, status_code=status.HTTP_201_CREATED)
async def book_rehearsal(
    rehearsal_data: RehearsalCreate,
    user_data: dict = Depends(get_current_user_from_request),
    service: RehearsalService = Depends(get_rehearsal_service),
):
    """Бронирование комнаты для репетиции."""
    current_user_id = user_data["user_id"]
    current_role = UserRole(user_data["role"])
    rehearsal = await service.book(rehearsal_data, current_user_id, current_role)
    return RehearsalCreateResponse(rehearsal=rehearsal, message="Репетиция успешно забронирована")


@router.post("/{rehearsal_id}/cancel", response_model=RehearsalCancelResponse)
async def cancel_rehearsal(
    rehearsal_id: int,
    user_data: dict = Depends(get_current_user_from_request),
    service: RehearsalService = Depends(get_rehearsal_service),
):
    """Отмена репетиции."""
    current_user_id = user_data["user_id"]
    current_role = UserRole(user_data["role"])
    await service.cancel(rehearsal_id, current_user_id, current_role)
    return RehearsalCancelResponse(message="Репетиция успешно отменена")
