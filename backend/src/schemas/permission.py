from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.schemas.common import NameDescriptionOut, Timestamp
from src.schemas.utils import sort_by_id


class PermissionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None


class PermissionOut(PermissionBase, Timestamp):
    id: int
    roles: list[NameDescriptionOut] = Field(default_factory=list)

    _sort = field_validator("roles")(sort_by_id)


class PermissionIn(PermissionBase): ...
