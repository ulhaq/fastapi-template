from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: EmailStr


class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime | None


class UserIn(UserBase):
    password: str
