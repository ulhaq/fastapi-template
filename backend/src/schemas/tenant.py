from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.common import Timestamp


class TenantBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1)]


class TenantOut(TenantBase, Timestamp):
    id: int


class TenantIn(TenantBase):
    email: EmailStr
    password: Annotated[str, Field(min_length=6)]


class TenantPatch(BaseModel):
    name: Annotated[str, Field(min_length=1)] | None = None
