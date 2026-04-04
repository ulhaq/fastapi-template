from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.common import Timestamp


class TenantBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1, max_length=255)]


class TenantOut(TenantBase, Timestamp):
    id: int


class TenantPatch(BaseModel):
    name: Annotated[str | None, Field(min_length=1, max_length=255)] = None
