from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.schemas.common import Timestamp
from src.schemas.role import RoleOut
from src.schemas.utils import sort_by_id


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1)]
    email: EmailStr


class UserOut(UserBase, Timestamp):
    id: int
    roles: list[RoleOut] = Field(default_factory=list)

    _sort = field_validator("roles")(sort_by_id)


class UserIn(UserBase):
    password: Annotated[str, Field(min_length=6)]


class EmailIn(BaseModel):
    email: EmailStr


class NewPasswordIn(BaseModel):
    password: Annotated[str, Field(min_length=6)]


class UserRoleIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)
