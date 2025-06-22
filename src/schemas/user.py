from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from src.schemas.common import Timestamp
from src.schemas.role import RoleOut
from src.schemas.utils import sort_by_id


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: EmailStr


class UserOut(UserBase, Timestamp):
    id: int
    roles: list[RoleOut] = Field(default_factory=list)

    _sort = field_validator("roles")(sort_by_id)


class UserIn(UserBase):
    password: str


class UserRoleIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)
