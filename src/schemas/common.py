from typing import Annotated, Generic, Sequence, TypeVar

from pydantic import BaseModel, Field, field_validator

from src.core.exceptions import ValidationException
from src.repositories.utils import ComparisonOperator

SchemaOutType = TypeVar("SchemaOutType", bound=BaseModel)  # pylint: disable=invalid-name


class PaginatedResponse(BaseModel, Generic[SchemaOutType]):
    items: Sequence[SchemaOutType]
    page_number: int
    page_size: int
    total: int


class Filter(BaseModel):
    v: Annotated[list, Field()]
    op: ComparisonOperator = Field(default=ComparisonOperator.EQUALS)

    @field_validator("op", mode="before")
    @classmethod
    def str_to_enum(cls, val: str):
        try:
            return ComparisonOperator(val)
        except ValueError as exc:
            raise ValidationException(f"Unsupported filter operator: {val}") from exc


class Filters(BaseModel):
    filters: Annotated[dict[str, Filter], Field()]
