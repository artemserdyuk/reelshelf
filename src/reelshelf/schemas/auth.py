from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
)


class UsernameRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=3, max_length=30)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()

        return value


class RegisterRequest(UsernameRequest):
    password: SecretStr = Field(min_length=8, max_length=128)


class LoginRequest(UsernameRequest):
    password: SecretStr = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    created_at: datetime


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
