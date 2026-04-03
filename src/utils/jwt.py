"""
Утилиты для работы с JWT-токенами.

Функции для создания, проверки и декодирования JWT-токенов.
"""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jose import jwt, JWTError, ExpiredSignatureError

logger = logging.getLogger(__name__)


def create_access_token(
    user_id: int,
    role: str,
    private_key_path: Path,
    algorithm: str = "RS256",
    expire_minutes: int = 30,
) -> str:
    """
    Создаёт JWT-токен для пользователя.

    Args:
        user_id: ID пользователя
        role: Роль пользователя (STUDENT, TEACHER, ADMIN)
        private_key_path: Путь к приватному ключу
        algorithm: Алгоритм шифрования
        expire_minutes: Время жизни токена в минутах

    Returns:
        str: JWT-токен
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    with open(private_key_path, "r") as f:
        private_key = f.read()
    return jwt.encode(payload, private_key, algorithm=algorithm)


def verify_token(
    token: str,
    public_key_path: Path,
    algorithm: str = "RS256",
) -> dict[str, Any]:
    """
    Проверяет и декодирует JWT-токен.

    Args:
        token: JWT-токен для проверки
        public_key_path: Путь к публичному ключу
        algorithm: Алгоритм шифрования

    Returns:
        dict: payload токена (sub, role, exp)

    Raises:
        ExpiredSignatureError: если токен истёк
        JWTError: если токен невалиден
    """
    with open(public_key_path, "r") as f:
        public_key = f.read()
    return jwt.decode(
        token,
        public_key,
        algorithms=[algorithm],
        options={"verify_exp": True},
    )


def decode_token_unsafe(token: str) -> dict[str, Any]:
    """
    Декодирует JWT-токен без проверки подписи.

    Используется только для получения данных из токена,
    когда проверка подписи не требуется.

    Args:
        token: JWT-токен

    Returns:
        dict: payload токена
    """
    return jwt.get_unverified_claims(token)
