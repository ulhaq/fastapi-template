from typing import Annotated, Callable

from fastapi import Depends, Query, Request
from fastapi.encoders import jsonable_encoder
from pydantic import Json

from src.core.exceptions import ValidationException
from src.enums import ComparisonOperator, ErrorCode
from src.schemas.common import Filters

COMMON_SORTING_FIELDS = ["id", "name", "created_at", "updated_at"]

SORTING_FIELDS_BY_PATH: dict[str, list[str]] = {
    "/roles": ["description"],
    "/permissions": ["description"],
}

COMMON_FILTERING_FIELDS = ["id", "name", "created_at", "updated_at"]

FILTERING_FIELDS_BY_PATH: dict[str, list[str]] = {
    "/roles": ["description"],
    "/permissions": ["description"],
}


def sort_query() -> Callable[..., list[str]]:
    def dependency(
        request: Request,
        sort: str = Query(
            default="id",
            description="Comma-separated list of fields to sort by.\n\n"
            "Use a leading `-` before a field name to indicate descending sort order.",
        ),
    ) -> list[str]:
        path = request.url.path
        valid_fields = SORTING_FIELDS_BY_PATH.get(path, []) + COMMON_SORTING_FIELDS

        if not sort:
            return []

        sort_fields = [field.strip() for field in sort.split(",")]
        invalid_fields = [
            field_name
            for field in sort_fields
            if (field_name := field.lstrip("-")) not in valid_fields
        ]

        if invalid_fields:
            raise ValidationException(
                f"Invalid sort value(s): {', '.join(invalid_fields)}. "
                f"Allowed: {', '.join(valid_fields)}",
                error_code=ErrorCode.PARAMETER_INVALID,
            )

        return sort_fields

    return dependency


def filters_query() -> Callable[..., dict[str, dict]]:
    def dependency(
        request: Request,
        filters: Json[dict[str, Filters]] | None = Query(
            default=None,
            description=(
                "Filter expression as a JSON string.\n\n"
                "Format:\n"
                '`{"field": {"v": [...], "op": "eq"}}`\n\n'
                "where:\n"
                "- `field` is the field name\n"
                "- `v` is a list of values\n"
                "- `op` is the operator\n\n"
                "Available operators are: "
                + ", ".join(f"`{op.value}`" for op in ComparisonOperator)
            ),
        ),
    ) -> dict[str, dict]:
        if not filters:
            return {}

        path = request.url.path
        valid_fields = FILTERING_FIELDS_BY_PATH.get(path, []) + COMMON_FILTERING_FIELDS
        invalid_fields = [field for field in filters if field not in valid_fields]

        if invalid_fields:
            raise ValidationException(
                f"Invalid filtering field(s): {', '.join(invalid_fields)}. "
                f"Allowed: {', '.join(valid_fields)}",
                error_code=ErrorCode.PARAMETER_INVALID,
            )

        return jsonable_encoder(filters)

    return dependency


SortQuery = Annotated[list[str], Depends(sort_query())]
FiltersQuery = Annotated[dict[str, dict], Depends(filters_query())]
PageSizeQuery = Annotated[int, Query(ge=10, le=100)]
PageNumberQuery = Annotated[int, Query(ge=1)]
