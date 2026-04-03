"""
Глобальный обработчик исключений для API.

Маппит исключения сервисного слоя в HTTP-статусы.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.services.exceptions import (
    ServiceError,
    AuthenticationError,
    TokenExpiredError,
    InvalidRoleError,
    UserNotFoundError,
    UserAlreadyExistsError,
    RoomNotFoundError,
    SlotNotFoundError,
    SlotConflictError,
    BookingNotFoundError,
    BookingConflictError,
    CapacityExceededError,
)


# Маппинг исключений в HTTP-статусы
EXCEPTION_STATUS_MAP = {
    # 400 Bad Request
    UserAlreadyExistsError: status.HTTP_400_BAD_REQUEST,
    CapacityExceededError: status.HTTP_400_BAD_REQUEST,
    
    # 401 Unauthorized
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    TokenExpiredError: status.HTTP_401_UNAUTHORIZED,
    
    # 403 Forbidden
    InvalidRoleError: status.HTTP_403_FORBIDDEN,
    
    # 404 Not Found
    UserNotFoundError: status.HTTP_404_NOT_FOUND,
    RoomNotFoundError: status.HTTP_404_NOT_FOUND,
    SlotNotFoundError: status.HTTP_404_NOT_FOUND,
    BookingNotFoundError: status.HTTP_404_NOT_FOUND,
    
    # 409 Conflict
    SlotConflictError: status.HTTP_409_CONFLICT,
    BookingConflictError: status.HTTP_409_CONFLICT,
}


async def service_exception_handler(request: Request, exc: ServiceError):
    """
    Обработчик исключений сервисного слоя.

    Возвращает JSON с полями:
    - error: тип исключения
    - detail: сообщение об ошибке
    """
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": type(exc).__name__,
            "detail": exc.message if hasattr(exc, "message") else str(exc),
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Обработчик ошибок валидации Pydantic.

    Возвращает JSON с полями:
    - error: "ValidationError"
    - detail: список ошибок
    """
    # Сериализуем ошибки, преобразуя ValueError в строки
    errors = []
    for err in exc.errors():
        serialized = {}
        for key, value in err.items():
            if key == "ctx" and isinstance(value, dict):
                # Преобразуем ValueError в строку в контексте ошибки
                serialized[key] = {
                    k: str(v) if isinstance(v, Exception) else v
                    for k, v in value.items()
                }
            else:
                serialized[key] = value
        errors.append(serialized)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "detail": errors,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Обработчик необработанных исключений.

    Возвращает 500 Internal Server Error.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "detail": "Внутренняя ошибка сервера",
        },
    )


def register_exception_handlers(app: FastAPI):
    """
    Регистрирует все обработчики исключений в приложении FastAPI.

    Вызывать один раз при создании приложения.
    """
    app.add_exception_handler(ServiceError, service_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
