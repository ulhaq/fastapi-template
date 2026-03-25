from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

from src.schemas.common import Timestamp


class TenantBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1)]


class TenantOut(TenantBase, Timestamp):
    id: int


class TenantIn(TenantBase):
    email: Annotated[EmailStr, StringConstraints(to_lower=True)]
    password: Annotated[str, Field(min_length=8)]


class TenantPatch(BaseModel):
    name: Annotated[str, Field(min_length=1)] | None = None
