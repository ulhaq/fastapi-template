import json
from typing import Annotated, Callable

from fastapi import Depends, Query, Request

from src.core.exceptions import ValidationException

COMMON_SORTING_FIELDS = [
    "id",
    "-id",
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
]

SORTING_FIELDS_BY_PATH: dict[str, list[str]] = {
    "/roles": ["description", "-description"],
    "/permissions": ["description", "-description"],
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
            default="id", description="Comma-separated list of sort fields."
        ),
    ) -> list[str]:
        path = request.url.path
        valid_fields = SORTING_FIELDS_BY_PATH.get(path, []) + COMMON_SORTING_FIELDS

        if not sort:
            return []

        sort_fields = [field.strip() for field in sort.split(",")]
        invalid_fields = [field for field in sort_fields if field not in valid_fields]

        if invalid_fields:
            raise ValidationException(
                detail=f"Invalid sort value(s): {', '.join(invalid_fields)}. "
                f"Allowed: {', '.join(valid_fields)}",
            )

        return sort_fields

    return dependency


def filters_query() -> Callable[..., dict[str, dict]]:
    def dependency(request: Request, filters: str = Query(default="{}")):
        if not filters:
            return {}

        try:
            filters = json.loads(filters)

            if not isinstance(filters, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValidationException(
                "The 'filters' parameter must be a JSON string with key-value pairs."
            ) from exc

        path = request.url.path
        valid_fields = FILTERING_FIELDS_BY_PATH.get(path, {}) + COMMON_FILTERING_FIELDS
        invalid_fields = [field for field in filters if field not in valid_fields]

        if invalid_fields:
            raise ValidationException(
                detail=f"Invalid filtering field(s): {', '.join(invalid_fields)}. "
                f"Allowed: {', '.join(valid_fields)}",
            )

        return filters

    return dependency


SortQuery = Annotated[list[str], Depends(sort_query())]
FiltersQuery = Annotated[dict[str, dict], Depends(filters_query())]
PageSizeQuery = Annotated[int, Query(ge=10, le=100)]
PageNumberQuery = Annotated[int, Query(ge=1)]
