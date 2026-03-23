from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import authenticate
from src.core.security import Auth
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.role import RoleIn, RoleOut, RolePatch, RolePermissionIn
from src.services.role import RoleService

# pylint: disable=too-many-arguments

router = APIRouter(prefix="/roles")


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_roles(
    *,
    service: Annotated[RoleService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[RoleOut]:
    current_user.authorize("read_role")
    return await service.paginate(
        RoleOut,
        PageQueryParams(
            sort=sort,
            filters=filters,
            page_size=page_size,
            page_number=page_number,
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_a_role(
    service: Annotated[RoleService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    role_in: RoleIn,
) -> RoleOut:
    current_user.authorize("create_role")
    return await service.create_role(role_in)


@router.put("/{identifier}", status_code=status.HTTP_200_OK)
async def update_a_role(
    service: Annotated[RoleService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
    role_in: RoleIn,
) -> RoleOut:
    current_user.authorize("update_role")
    return await service.update_role(identifier, role_in)


@router.patch("/{identifier}", status_code=status.HTTP_200_OK)
async def patch_a_role(
    service: Annotated[RoleService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
    role_in: RolePatch,
) -> RoleOut:
    current_user.authorize("update_role")
    return await service.patch_role(identifier, role_in)


@router.get("/{identifier}", status_code=status.HTTP_200_OK)
async def retrieve_a_role(
    service: Annotated[RoleService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
) -> RoleOut:
    current_user.authorize("read_role")
    return await service.get_role(identifier)


@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_role(
    service: Annotated[RoleService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
) -> None:
    current_user.authorize("delete_role")
    await service.delete_role(identifier)


@router.post("/{identifier}/permissions", status_code=status.HTTP_200_OK)
async def manage_permissions_of_a_role(
    service: Annotated[RoleService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
    role_permission_in: RolePermissionIn,
) -> RoleOut:
    current_user.authorize("manage_role_permission")
    return await service.manage_permissions(identifier, role_permission_in)
