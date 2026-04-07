"""
Скрипт создания первого администратора.

Запускается автоматически при docker compose up --build.
Для изменения данных админа отредактируйте константы в начале файла.
"""

import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.database import session_factory
from src.repositories.UserRepository import UserRepository
from src.utils.security import get_password_hash

# Импортируем все модели, чтобы SQLAlchemy зарегистрировал связи
from src.models.User import User  # noqa: F401
from src.models.Room import Room  # noqa: F401
from src.models.LessonSlot import LessonSlot  # noqa: F401
from src.models.LessonBooking import LessonBooking  # noqa: F401
from src.models.RehearsalBooking import RehearsalBooking  # noqa: F401
from src.models.Notification import Notification  # noqa: F401

# =============================================================================
# Данные администратора — измените при необходимости
# =============================================================================
ADMIN_PHONE = "+79991234567"
ADMIN_FULL_NAME = "Администратор"
ADMIN_PASSWORD = "admin123456"
# =============================================================================


async def create_admin_if_not_exists():
    """Создаёт пользователя с ролью ADMIN, если его ещё нет."""
    async with session_factory() as session:
        repo = UserRepository(session)

        existing = await repo.get_by_phone(ADMIN_PHONE)
        if existing is not None:
            print(f"Администратор {ADMIN_PHONE} уже существует, пропускаем.")
            return

        await repo.create_user(
            phone=ADMIN_PHONE,
            full_name=ADMIN_FULL_NAME,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            role="ADMIN",
        )
        await session.commit()
        print(f"Администратор {ADMIN_FULL_NAME} ({ADMIN_PHONE}) успешно создан.")


if __name__ == "__main__":
    asyncio.run(create_admin_if_not_exists())
