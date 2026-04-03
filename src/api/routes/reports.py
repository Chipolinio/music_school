"""
API роуты для отчётов.
"""

from datetime import date
from fastapi import APIRouter, Depends, Response
from fastapi.responses import Response as FastAPIResponse

from src.api.deps import get_report_service, ReportService
from src.schemas.Report import (
    ReportPeriodRequest,
    LessonCountByTeacherResponse,
    UserAttendanceResponse,
    PeakHoursResponse,
)


router = APIRouter(prefix="/reports", tags=["Отчёты"])


@router.get("/lessons-by-teacher", response_model=list[LessonCountByTeacherResponse])
async def get_lesson_count_by_teacher(
    start_date: date,
    end_date: date,
    service: ReportService = Depends(get_report_service),
):
    """Количество уроков по преподавателям за период."""
    return await service.get_lesson_count_by_teacher(start_date, end_date)


@router.get("/lessons-by-teacher/csv")
async def export_lesson_count_csv(
    start_date: date,
    end_date: date,
    service: ReportService = Depends(get_report_service),
):
    """Экспорт отчёта по урокам в CSV."""
    csv_data = await service.export_lesson_count_csv(start_date, end_date)
    return FastAPIResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=lesson_count.csv"},
    )


@router.get("/attendance/{user_id}", response_model=UserAttendanceResponse)
async def get_user_attendance(
    user_id: int,
    start_date: date,
    end_date: date,
    service: ReportService = Depends(get_report_service),
):
    """Посещаемость пользователя за период."""
    return await service.get_user_attendance(user_id, start_date, end_date)


@router.get("/attendance/{user_id}/csv")
async def export_attendance_csv(
    user_id: int,
    start_date: date,
    end_date: date,
    service: ReportService = Depends(get_report_service),
):
    """Экспорт посещаемости в CSV."""
    csv_data = await service.export_attendance_csv(user_id, start_date, end_date)
    return FastAPIResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=attendance.csv"},
    )


@router.get("/peak-hours", response_model=list[PeakHoursResponse])
async def get_peak_hours(
    start_date: date,
    end_date: date,
    service: ReportService = Depends(get_report_service),
):
    """Популярные часы для уроков."""
    return await service.get_peak_hours(start_date, end_date)


@router.get("/peak-hours/csv")
async def export_peak_hours_csv(
    start_date: date,
    end_date: date,
    service: ReportService = Depends(get_report_service),
):
    """Экспорт популярных часов в CSV."""
    csv_data = await service.export_peak_hours_csv(start_date, end_date)
    return FastAPIResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=peak_hours.csv"},
    )
