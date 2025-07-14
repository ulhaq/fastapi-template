from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.common import NameDescriptionOut, Timestamp
from src.schemas.utils import sort_by_id


class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None


class RoleOut(RoleBase, Timestamp):
    id: int
    permissions: list[NameDescriptionOut] = Field(default_factory=list)

    _sort = field_validator("permissions")(sort_by_id)


class RoleIn(RoleBase): ...


class RolePermissionIn(BaseModel):
    permission_ids: list[int] = Field(default_factory=list)
