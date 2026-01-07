from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import authenticate
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.permission import PermissionIn, PermissionOut
from src.services.permission import PermissionService

router = APIRouter()


@router.get(
    "/permissions", dependencies=[Depends(authenticate)], status_code=status.HTTP_200_OK
)
async def get_all_permissions(
    service: Annotated[PermissionService, Depends()],
    sort: SortQuery,
    filters: FiltersQuery,
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
        ),
    )


@router.post(
    "/permissions",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_201_CREATED,
)
async def create_a_permission(
    service: Annotated[PermissionService, Depends()], permission_in: PermissionIn
) -> PermissionOut:
    return await service.create_permission(permission_in)


@router.put(
    "/permissions/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def update_a_permission(
    service: Annotated[PermissionService, Depends()],
    identifier: Annotated[int, Path()],
    permission_in: PermissionIn,
) -> PermissionOut:
    return await service.update_permission(identifier, permission_in)


@router.get(
    "/permissions/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def retrieve_a_permission(
    service: Annotated[PermissionService, Depends()], identifier: Annotated[int, Path()]
) -> PermissionOut:
    return await service.get_permission(identifier)


@router.delete(
    "/permissions/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_a_permission(
    service: Annotated[PermissionService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete_permission(identifier)
