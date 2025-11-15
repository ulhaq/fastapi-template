from datetime import datetime, timezone
from typing import Annotated, Any, Sequence

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field

from src.enums import ErrorCode
from src.repositories.utils import ComparisonOperator


class ErrorResponse(BaseModel):
    time: Annotated[datetime, Field()]
    path: Annotated[str, Field()]
    method: Annotated[str, Field()]
    error_code: Annotated[str, Field()]
    msg: Annotated[str, Field()]

    def __init__(
        self, request: Request, error_code: ErrorCode, msg: str, **kwargs: Any
    ) -> None:
        super().__init__(
            time=datetime.now(timezone.utc),
            path=str(request.url),
            method=request.method,
            error_code=error_code.code,
            msg=msg,
            **kwargs,
        )


class ValidationDetail(BaseModel):
    error_code: Annotated[str, Field()]
    field: Annotated[list[str | int], Field()]
    msg: Annotated[str, Field()]
    ctx: Annotated[Any, Field()]


class ValidationErrorResponse(ErrorResponse):
    errors: Annotated[list[ValidationDetail], Field()]

    def __init__(
        self, request: Request, error_code: ErrorCode, msg: str, **kwargs: Any
    ) -> None:
        kwargs["errors"] = [
            ValidationDetail(
                error_code=error["type"],
                field=error["loc"],
                msg=error["msg"],
                ctx=jsonable_encoder(error["ctx"]) if "ctx" in error else {},
            )
            for error in kwargs.get("errors", {})
        ]

        super().__init__(request=request, error_code=error_code, msg=msg, **kwargs)


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
