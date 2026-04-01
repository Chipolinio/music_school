from typing import Annotated, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator, StrictInt

from src.utils.validators import name_validator, phone_validator

class UserRole(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMIN = "ADMIN"

class UserBase(BaseModel):
    phone: Annotated[str, Field(
        ...,
        description="Номер телефона в международном формате",
        examples=["+79991234567"]
    )]
    full_name: Annotated[str, Field(
        ...,
        min_length=2,
        max_length=255,
        description="ФИО пользователя"
    )]
    role: Annotated[UserRole, Field(
        UserRole.STUDENT,
        description="Роль в системе"
    )]

    @field_validator("full_name", mode="after")
    @classmethod
    def validate_full_name(cls, v):
        return name_validator(v)

    @field_validator("phone", mode="after")
    @classmethod
    def validate_phone(cls, v):
        return phone_validator(v)

    model_config = ConfigDict(str_strip_whitespace=True)

class UserCreate(UserBase):
    password: Annotated[str, Field(
        ...,
        min_length=8,
        max_length=100,
        description="Пароль пользователя (будет захэширован)"
    )]

class UserResponse(UserBase):
    id: Annotated[StrictInt, Field(..., ge=1, description="Внутренний ID в БД")]
    is_active: Annotated[bool, Field(..., description="Статус активности аккаунта")]

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    phone: Annotated[Optional[str], Field(None, description="Новый номер телефона")]
    full_name: Annotated[Optional[str], Field(None, min_length=2, max_length=255)]
    role: Annotated[Optional[UserRole], Field(None)]
    is_active: Annotated[Optional[bool], Field(None)]

    @field_validator("full_name", mode="after")
    @classmethod
    def validate_full_name(cls, v):
        if v is None: return v
        return name_validator(v)

    @field_validator("phone", mode="after")
    @classmethod
    def validate_phone(cls, v):
        if v is None: return v
        return phone_validator(v)

    model_config = ConfigDict(str_strip_whitespace=True)