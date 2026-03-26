from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

from src.core.exceptions import ValidationException
from src.schemas.common import Timestamp
from src.schemas.role import RoleOut
from src.schemas.utils import sort_by_id


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1)]
    email: Annotated[EmailStr, StringConstraints(to_lower=True)]


class UserOut(UserBase, Timestamp):
    id: int
    roles: Annotated[list[RoleOut], AfterValidator(sort_by_id)] = Field(
        default_factory=list
    )


class UserIn(UserBase):
    password: Annotated[str, Field(min_length=8)]


class UserPatch(BaseModel):
    name: Annotated[str, Field(min_length=1)] | None = None
    email: EmailStr | None = None


class EmailIn(BaseModel):
    email: Annotated[EmailStr, StringConstraints(to_lower=True)]


class ResetPasswordIn(BaseModel):
    token: Annotated[str, Field()]
    password: Annotated[str, Field(min_length=8)]


class ChangePasswordIn(BaseModel):
    password: Annotated[str, Field(min_length=1)]
    new_password: Annotated[str, Field(min_length=8)]
    confirm_password: Annotated[str, Field()]

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValidationException("Passwords do not match")
        return self


class UserRoleIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)
