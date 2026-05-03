from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.organization import OrganizationOut
from src.schemas.role import RoleOut
from src.schemas.types import ConstrainedEmail, NonEmptyStr


class AdminUserOrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    created_at: datetime
    updated_at: datetime | None
    organizations: list[AdminUserOrgOut] = Field(default_factory=list)


class AdminOrganizationOut(OrganizationOut):
    plan_name: str | None = None
    subscription_status: str | None = None


class OrgMemberOut(BaseModel):
    user_id: int
    name: str
    email: str
    roles: list[RoleOut]


class AddMemberIn(BaseModel):
    email: ConstrainedEmail
    role_ids: Annotated[list[int], Field(default_factory=list)] = Field(
        default_factory=list
    )


class AdminOrganizationCreate(BaseModel):
    name: Annotated[NonEmptyStr, Field(max_length=255)]
