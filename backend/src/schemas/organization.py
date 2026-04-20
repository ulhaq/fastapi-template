from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.common import Timestamp


class OrganizationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1, max_length=255)]


class OrganizationOut(OrganizationBase, Timestamp):
    id: int


class MyOrganizationOut(OrganizationOut):
    is_owner: bool = False


class OrganizationPatch(BaseModel):
    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None


class TransferOwnershipIn(BaseModel):
    user_id: int
