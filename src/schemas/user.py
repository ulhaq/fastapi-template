from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.auth import RoleOut


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: EmailStr


class UserOut(UserBase):
    id: int
    roles: list[RoleOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None


class UserIn(UserBase):
    password: str


class UserRoleIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)
