"""
Утилиты безопасности: JWT-токены, хэширование паролей, cookies.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from settings import settings
from starlette.responses import Response


def _ensure_jwt_keys():
    """
    Гарантирует существование JWT ключей.
    Если ключей нет — генерирует их.
    """
    private_key_path = settings.JWT_PRIVATE_KEY
    public_key_path = settings.JWT_PUBLIC_KEY
    
    # Если ключи уже есть — ничего не делаем
    if private_key_path.exists() and public_key_path.exists():
        return
    
    # Создаём директорию
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Генерируем пару ключей
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    public_key = private_key.public_key()
    
    # Сохраняем приватный ключ
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key_path.write_bytes(private_pem)
    
    # Сохраняем публичный ключ
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_key_path.write_bytes(public_pem)


# Генерируем ключи при импорте модуля
_ensure_jwt_keys()

JWT_PRIVATE_KEY = settings.JWT_PRIVATE_KEY.read_text()
JWT_PUBLIC_KEY = settings.JWT_PUBLIC_KEY.read_text()


def get_password_hash(password: str) -> str:
    """Хэширует пароль с помощью bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хэшу."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_token(data_dict: dict, duration: int = 1800) -> str:
    """
    Создаёт JWT-токен.

    Args:
        data_dict: Данные для токена
        duration: Время жизни в секундах (по умолчанию 30 минут)

    Returns:
        str: JWT-токен
    """
    data = data_dict.copy()
    expire = datetime.now(timezone.utc) + timedelta(seconds=duration)
    data.update({"exp": expire})
    return jwt.encode(data, JWT_PRIVATE_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Декодирует JWT-токен.

    Args:
        token: JWT-токен

    Returns:
        dict: payload токена
    """
    return jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[settings.ALGORITHM])


def set_auth_token(
    response: Response,
    token: str,
    key: str,
    max_age: int = 1800,
):
    """
    Устанавливает cookie с JWT-токеном.

    Args:
        response: HTTP-ответ
        token: JWT-токен
        key: Имя cookie
        max_age: Время жизни cookie в секундах
    """
    response.set_cookie(
        key=key,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=max_age,
        path="/",
        domain=None,
    )
