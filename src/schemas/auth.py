from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None


class SimpleRoleOut(RoleBase):
    id: int


class RoleOut(SimpleRoleOut):
    permissions: list["SimplePermissionOut"] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None


class RoleIn(RoleBase):
    pass


class RolePermissionIn(BaseModel):
    permission_ids: list[int] = Field(default_factory=list)


class PermissionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None


class SimplePermissionOut(PermissionBase):
    id: int


class PermissionOut(SimplePermissionOut):
    roles: list[SimpleRoleOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime | None


class PermissionIn(PermissionBase):
    pass
