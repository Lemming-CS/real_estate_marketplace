from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.db.enums import UserStatus

LocaleCode = Literal["en", "ru"]


class AuthUserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    email: EmailStr
    username: str
    full_name: str
    locale: str
    status: UserStatus
    roles: list[str]
    profile_image_path: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    access_token_expires_in: int
    refresh_token: str
    refresh_token_expires_in: int
    user: AuthUserSchema


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    password: str = Field(min_length=8, max_length=128)
    locale: LocaleCode = "en"

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=16)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    debug_reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=16)
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(BaseModel):
    message: str

