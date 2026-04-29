from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from src.core.exceptions import ValidationException
from src.schemas.common import Timestamp
from src.schemas.role import RoleOut
from src.schemas.types import ConstrainedEmail, NonEmptyStr, Password
from src.schemas.utils import sort_by_id


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: NonEmptyStr
    email: ConstrainedEmail


class UserOut(UserBase, Timestamp):
    id: int
    roles: Annotated[list[RoleOut], AfterValidator(sort_by_id)] = Field(
        default_factory=list
    )


class UserPatch(BaseModel):
    name: NonEmptyStr | None = None
    email: ConstrainedEmail | None = None


class EmailIn(BaseModel):
    email: ConstrainedEmail


class SwitchOrganizationIn(BaseModel):
    organization_id: int


class ResetPasswordIn(BaseModel):
    token: str
    password: Password


class ChangePasswordIn(BaseModel):
    password: NonEmptyStr
    new_password: Password
    confirm_password: str

    @model_validator(mode="after")
    def check_passwords_match(self) -> Self:
        if self.new_password != self.confirm_password:
            raise ValidationException("Passwords do not match")
        return self


class UserRoleIn(BaseModel):
    role_ids: list[int] = Field(default_factory=list)


class RegisterOut(BaseModel):
    message: str


class VerifyEmailIn(BaseModel):
    token: str


class SetupTokenOut(BaseModel):
    setup_token: str


class CompleteRegistrationIn(BaseModel):
    setup_token: str
    name: NonEmptyStr
    password: Password


class InviteUserIn(BaseModel):
    email: ConstrainedEmail
    role_ids: list[int] = Field(default_factory=list)


class CompleteInviteIn(BaseModel):
    invite_token: str
    name: NonEmptyStr | None = None
    password: Password | None = None


class InviteStatusIn(BaseModel):
    token: str


class InviteStatusOut(BaseModel):
    email: str
    user_exists: bool
