"""
API роуты для бронирования уроков.
"""

from fastapi import APIRouter, Depends, status

from src.api.deps import get_booking_service, BookingService, get_current_user_from_request
from src.schemas.User import UserRole
from src.schemas.LessonBooking import LessonResponse, LessonCreate, LessonBookingListResponse, LessonCreateResponse, LessonCancelResponse


router = APIRouter(prefix="/bookings", tags=["Бронирование уроков"])


@router.get("/{booking_id}", response_model=LessonResponse)
async def get_booking(
    booking_id: int,
    service: BookingService = Depends(get_booking_service),
):
    """Получение брони по ID."""
    return await service.get_by_id(booking_id)


@router.get("/student/{student_id}", response_model=LessonBookingListResponse)
async def get_student_bookings(
    student_id: int,
    service: BookingService = Depends(get_booking_service),
):
    """Получение всех броней студента."""
    bookings = await service.get_student(student_id)
    return LessonBookingListResponse(bookings=bookings, total=len(bookings))


@router.post("/", response_model=LessonCreateResponse, status_code=status.HTTP_201_CREATED)
async def book_lesson(
    booking_data: LessonCreate,
    user_data: dict = Depends(get_current_user_from_request),
    service: BookingService = Depends(get_booking_service),
):
    """Запись на урок."""
    current_user_id = user_data["user_id"]
    current_role = UserRole(user_data["role"])
    booking = await service.book(booking_data, current_user_id, current_role)
    return LessonCreateResponse(booking=booking, message="Успешная запись на урок")


@router.post("/{booking_id}/cancel", response_model=LessonCancelResponse)
async def cancel_booking(
    booking_id: int,
    user_data: dict = Depends(get_current_user_from_request),
    service: BookingService = Depends(get_booking_service),
):
    """Отмена брони."""
    current_user_id = user_data["user_id"]
    current_role = UserRole(user_data["role"])
    await service.cancel(booking_id, current_user_id, current_role)
    return LessonCancelResponse(message="Бронь успешно отменена")
