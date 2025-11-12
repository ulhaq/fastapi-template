from typing import Annotated
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from src.schemas.common import NameDescriptionOut, Timestamp
from src.schemas.utils import sort_by_id


class RoleBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None


class RoleOut(RoleBase, Timestamp):
    id: int
    permissions: Annotated[list[NameDescriptionOut], AfterValidator(sort_by_id)] = (
        Field(default_factory=list)
    )


class RoleIn(RoleBase): ...


class RolePermissionIn(BaseModel):
    permission_ids: list[int] = Field(default_factory=list)
