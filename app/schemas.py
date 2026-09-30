from datetime import datetime
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


def remove_duplicates(v) -> list:
    if isinstance(v, list):
        return list(dict.fromkeys(v))
    return v


TagName = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=3, max_length=50, to_lower=True
    ),
]


TagList = Annotated[
    list[TagName],
    AfterValidator(remove_duplicates),
]


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
    refresh_token: str
    token_type: str = Field(default="bearer")


class TokenRefresh(BaseModel):
    refresh_token: str


class ProjectCreate(BaseModel):
    title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
    ]


class ProjectUpdate(BaseModel):
    title: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
        ]
        | None
    ) = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        if v is None:
            raise ValueError("The title cannot be None.")
        return v


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    owner_id: UUID
    created_at: datetime


class TaskCreate(BaseModel):
    title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
    ]
    status: TaskStatus = Field(default=TaskStatus.TODO)
    assignee_id: UUID | None = None
    project_id: UUID
    tags: TagList = None  # type: ignore


class TaskUpdate(BaseModel):
    title: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=3, max_length=255)
        ]
        | None
    ) = None
    status: TaskStatus | None = None
    assignee_id: UUID | None = None
    tags: TagList = None  # type: ignore


class TagCreate(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)
    ]


class TagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    creator_id: UUID
    assignee_id: UUID | None
    title: str
    status: TaskStatus
    tags: list[TagRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
