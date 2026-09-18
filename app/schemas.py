from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)


def pass_len(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password length is below the minimum allowed.")
    if len(password) > 50:
        raise ValueError("Password length exceeds the allowed maximum.")
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password length exceeds the byte limit.")
    return password


def username_len(username: str) -> str:
    if len(username) < 3:
        raise ValueError("Username length is too short.")
    if len(username) > 30:
        raise ValueError("Username length is too long.")
    return username


class UserCreate(BaseModel):
    email: EmailStr
    username: Annotated[str, AfterValidator(username_len)]
    password: Annotated[str, AfterValidator(pass_len)]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    username: str
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
