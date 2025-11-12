from typing import Annotated
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.schemas.common import Timestamp


class CompanyBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, Field(min_length=1)]


class CompanyOut(CompanyBase, Timestamp):
    id: int


class CompanyIn(CompanyBase):
    email: EmailStr
    password: Annotated[str, Field(min_length=6)]
