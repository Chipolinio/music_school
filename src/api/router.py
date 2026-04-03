"""
Главный роутер API, объединяющий все endpoints.
"""

from fastapi import APIRouter

from src.api.routes.auth import router as auth_router
from src.api.routes.users import router as users_router
from src.api.routes.rooms import router as rooms_router
from src.api.routes.schedule import router as schedule_router
from src.api.routes.bookings import router as bookings_router
from src.api.routes.rehearsals import router as rehearsals_router
from src.api.routes.notifications import router as notifications_router
from src.api.routes.reports import router as reports_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(rooms_router)
api_router.include_router(schedule_router)
api_router.include_router(bookings_router)
api_router.include_router(rehearsals_router)
api_router.include_router(notifications_router)
api_router.include_router(reports_router)
