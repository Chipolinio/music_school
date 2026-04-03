"""
Утилиты для хэширования паролей.

Функции для хэширования и проверки паролей с использованием bcrypt.
"""

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Хэширует пароль с помощью bcrypt.

    Args:
        password: Пароль в открытом виде

    Returns:
        str: Хэш пароля
    """
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие пароля хэшу.

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хэш пароля

    Returns:
        bool: True, если пароль совпадает
    """
    return _pwd_context.verify(plain_password, hashed_password)
