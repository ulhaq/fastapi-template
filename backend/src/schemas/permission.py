from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from src.schemas.common import NameDescriptionOut, Timestamp
from src.schemas.utils import sort_by_id


class PermissionBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None


class PermissionOut(PermissionBase, Timestamp):
    id: int
    roles: Annotated[list[NameDescriptionOut], AfterValidator(sort_by_id)] = Field(
        default_factory=list
    )


class PermissionIn(PermissionBase): ...
