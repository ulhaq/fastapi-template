from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from src.core.exceptions import ValidationException
from src.schemas.common import Timestamp
from src.schemas.role import RoleOut
from src.schemas.utils import sort_by_id


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1)]
    email: EmailStr


class UserOut(UserBase, Timestamp):
    id: int
    roles: Annotated[list[RoleOut], AfterValidator(sort_by_id)] = Field(
        default_factory=list
    )


class UserIn(UserBase):
    password: Annotated[str, Field(min_length=6)]
    company_id: Annotated[int, Field()]


class EmailIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: Annotated[str, Field()]
    password: Annotated[str, Field(min_length=6)]


class ChangePasswordIn(BaseModel):
    password: Annotated[str, Field(min_length=6)]
    new_password: Annotated[str, Field(min_length=6)]
    confirm_password: Annotated[str, Field()]

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValidationException("Passwords do not match")
        return self


class UserRoleIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)
