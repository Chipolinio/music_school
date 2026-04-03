"""
API роуты для аутентификации и регистрации.
"""

from fastapi import APIRouter, Depends, Request, Response, status

from src.api.deps import get_auth_service, AuthService, get_current_user_from_request
from src.schemas.User import UserCreate, UserResponse
from src.schemas.Auth import LoginRequest, AuthResponse, LogoutResponse, TokenVerifyResponse


router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    service: AuthService = Depends(get_auth_service),
    response: Response = None,
):
    """
    Регистрация нового пользователя.

    После успешной регистрации устанавливается cookie с JWT-токеном.
    """
    user_response, token = await service.register(user_data)

    response.set_cookie(
        key="jwt_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=1800,
        path="/",
    )

    return AuthResponse(user=user_response, message="Пользователь успешно зарегистрирован")


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
    response: Response = None,
):
    """
    Вход пользователя.

    После успешного входа устанавливается cookie с JWT-токеном.
    """
    user_response, token = await service.login(login_data.phone, login_data.password)

    response.set_cookie(
        key="jwt_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=1800,
        path="/",
    )

    return AuthResponse(user=user_response, message="Успешный вход")


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    service: AuthService = Depends(get_auth_service),
    response: Response = None,
):
    """
    Выход пользователя.

    Очищает cookie с JWT-токеном.
    """
    token = request.cookies.get("jwt_token")
    if token:
        service.logout(token)

    response.delete_cookie(
        key="jwt_token",
        path="/",
    )

    return LogoutResponse(message="Успешный выход")


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_data: dict = Depends(get_current_user_from_request),
):
    """
    Получение данных текущего пользователя.

    Требуется авторизация (JWT-токен в cookies).
    """
    return user_data["user"]


@router.post("/verify-token", response_model=TokenVerifyResponse)
async def verify_token(
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """
    Проверка валидности JWT-токена.
    """
    token = request.cookies.get("jwt_token")

    if not token:
        return TokenVerifyResponse(valid=False, payload={})

    try:
        payload = service.verify_token(token)
        return TokenVerifyResponse(
            valid=True,
            payload={
                "user_id": int(payload.get("sub")),
                "role": payload.get("role"),
                "exp": payload.get("exp"),
            },
        )
    except Exception:
        return TokenVerifyResponse(valid=False, payload={})
