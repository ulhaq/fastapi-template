from datetime import datetime
from typing import Annotated, Sequence

from pydantic import BaseModel, ConfigDict, Field

from src.repositories.utils import ComparisonOperator


class Timestamp(BaseModel):
    created_at: datetime
    updated_at: datetime | None


class NameDescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


class PaginatedResponse[SchemaOutType: BaseModel](BaseModel):  # pylint: disable=invalid-name
    items: Sequence[SchemaOutType]
    page_number: int
    page_size: int
    total: int


class Filters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    v: Annotated[list, Field()]
    op: ComparisonOperator = Field(default=ComparisonOperator.EQUALS)


class PageQueryParams(BaseModel):
    sort: Annotated[list[str], Field()]
    filters: Annotated[dict[str, dict], Field()]
    page_size: Annotated[int, Field()]
    page_number: Annotated[int, Field()]
