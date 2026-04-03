"""
Кастомные исключения сервисного слоя.

Все исключения сервисного слоя наследуются от базового ServiceError.
Используются для явной обработки ошибок бизнес-логики.
"""


class ServiceError(Exception):
    """Базовый класс для всех исключений сервисного слоя."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


# === Исключения аутентификации ===


class AuthenticationError(ServiceError):
    """Неверные учётные данные."""

    def __init__(self, message: str = "Неверные учётные данные"):
        super().__init__(message)


class TokenExpiredError(ServiceError):
    """JWT-токен истёк."""

    def __init__(self, message: str = "JWT-токен истёк"):
        super().__init__(message)


class InvalidRoleError(ServiceError):
    """Недостаточно прав для операции."""

    def __init__(self, message: str = "Недостаточно прав для выполнения операции"):
        super().__init__(message)


# === Исключения сущностей ===


class UserNotFoundError(ServiceError):
    """Пользователь не найден."""

    def __init__(self, user_id: int | None = None, phone: str | None = None):
        if user_id:
            message = f"Пользователь с ID {user_id} не найден"
        elif phone:
            message = f"Пользователь с телефоном {phone} не найден"
        else:
            message = "Пользователь не найден"
        super().__init__(message)
        self.user_id = user_id
        self.phone = phone


class UserAlreadyExistsError(ServiceError):
    """Пользователь с таким телефоном уже существует."""

    def __init__(self, phone: str):
        super().__init__(f"Пользователь с телефоном {phone} уже существует")
        self.phone = phone


class RoomNotFoundError(ServiceError):
    """Комната не найдена."""

    def __init__(self, room_id: int):
        super().__init__(f"Комната с ID {room_id} не найдена")
        self.room_id = room_id


class SlotNotFoundError(ServiceError):
    """Слот урока не найден."""

    def __init__(self, slot_id: int):
        super().__init__(f"Слот урока с ID {slot_id} не найден")
        self.slot_id = slot_id


class SlotConflictError(ServiceError):
    """Конфликт времени (комната или преподаватель заняты)."""

    def __init__(self, message: str):
        super().__init__(message)


class BookingNotFoundError(ServiceError):
    """Бронь не найдена."""

    def __init__(self, booking_id: int):
        super().__init__(f"Бронь с ID {booking_id} не найдена")
        self.booking_id = booking_id


class BookingConflictError(ServiceError):
    """Конфликт бронирования (время пересекается)."""

    def __init__(self, message: str):
        super().__init__(message)


class CapacityExceededError(ServiceError):
    """Превышена вместимость слота."""

    def __init__(self, slot_id: int, max_participants: int):
        super().__init__(
            f"Превышена вместимость слота {slot_id} (максимум {max_participants} участников)"
        )
        self.slot_id = slot_id
        self.max_participants = max_participants
