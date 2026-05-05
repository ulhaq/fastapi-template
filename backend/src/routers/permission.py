from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import require_permission
from src.core.security import Auth
from src.enums import Permission
from src.routers.query_options import (
    PageNumberQuery,
    PageSizeQuery,
    SearchQuery,
    filters_query,
    sort_query,
)
from src.schemas.common import FilterItem, PageQueryParams, PaginatedResponse
from src.schemas.permission import PermissionOut
from src.services.permission import PermissionService

router = APIRouter(prefix="/permissions")


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_permissions(
    *,
    service: Annotated[PermissionService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_PERMISSION))],
    sort: Annotated[list[str], Depends(sort_query(["description"]))],
    filters: Annotated[list[FilterItem], Depends(filters_query(["description"]))],
    q: SearchQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[PermissionOut]:
    return await service.paginate(
        PermissionOut,
        PageQueryParams(
            sort=sort,
            filters=filters,
            page_size=page_size,
            page_number=page_number,
            search=q,
        ),
    )


@router.get("/{identifier}", status_code=status.HTTP_200_OK)
async def retrieve_a_permission(
    service: Annotated[PermissionService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_PERMISSION))],
    identifier: Annotated[int, Path()],
) -> PermissionOut:
    return await service.get_permission(identifier)
