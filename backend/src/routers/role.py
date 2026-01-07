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
from src.schemas.role import RoleIn, RoleOut, RolePermissionIn
from src.services.role import RoleService

router = APIRouter()


@router.get(
    "/roles", dependencies=[Depends(authenticate)], status_code=status.HTTP_200_OK
)
async def get_all_roles(
    service: Annotated[RoleService, Depends()],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[RoleOut]:
    return await service.paginate(
        RoleOut,
        PageQueryParams(
            sort=sort,
            filters=filters,
            page_size=page_size,
            page_number=page_number,
        ),
    )


@router.post(
    "/roles", dependencies=[Depends(authenticate)], status_code=status.HTTP_201_CREATED
)
async def create_a_role(
    service: Annotated[RoleService, Depends()], role_in: RoleIn
) -> RoleOut:
    return await service.create_role(role_in)


@router.put(
    "/roles/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def update_a_role(
    service: Annotated[RoleService, Depends()],
    identifier: Annotated[int, Path()],
    role_in: RoleIn,
) -> RoleOut:
    return await service.update_role(identifier, role_in)


@router.get(
    "/roles/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def retrieve_a_role(
    service: Annotated[RoleService, Depends()], identifier: Annotated[int, Path()]
) -> RoleOut:
    return await service.get_role(identifier)


@router.delete(
    "/roles/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_a_role(
    service: Annotated[RoleService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete_role(identifier)


@router.post(
    "/roles/{identifier}/permissions",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def manage_permissions_of_a_role(
    service: Annotated[RoleService, Depends()],
    identifier: Annotated[int, Path()],
    role_permission_in: RolePermissionIn,
) -> RoleOut:
    return await service.manage_permissions(identifier, role_permission_in)
