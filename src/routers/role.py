from typing import Annotated

from fastapi import APIRouter, Depends, Path

from src.core.dependencies import authenticate
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.common import Filters, PaginatedResponse
from src.schemas.role import RoleIn, RoleOut, RolePermissionIn
from src.services.role import RoleService

router = APIRouter()


@router.get("/roles", dependencies=[Depends(authenticate)], status_code=200)
async def get_all_roles(
    service: Annotated[RoleService, Depends()],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[RoleOut]:
    return await service.paginate(
        RoleOut,
        sort=sort,
        filters=Filters.model_validate({"filters": filters}),
        page_size=page_size,
        page_number=page_number,
    )


@router.post(
    "/roles",
    dependencies=[Depends(authenticate)],
    status_code=201,
    response_model=RoleOut,
)
async def create_a_role(service: Annotated[RoleService, Depends()], role_in: RoleIn):
    return await service.create_role(role_in)


@router.put(
    "/roles/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=RoleOut,
)
async def update_a_role(
    service: Annotated[RoleService, Depends()],
    identifier: Annotated[int, Path()],
    role_in: RoleIn,
):
    return await service.update_role(identifier, role_in)


@router.get(
    "/roles/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=RoleOut,
)
async def retrieve_a_role(
    service: Annotated[RoleService, Depends()], identifier: Annotated[int, Path()]
):
    return await service.get_role(identifier)


@router.delete(
    "/roles/{identifier}", dependencies=[Depends(authenticate)], status_code=204
)
async def delete_a_role(
    service: Annotated[RoleService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete_role(identifier)


@router.post(
    "/roles/{identifier}/permissions",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=RoleOut,
)
async def manage_permissions_of_a_role(
    service: Annotated[RoleService, Depends()],
    identifier: Annotated[int, Path()],
    role_permission_in: RolePermissionIn,
):
    return await service.manage_permissions(identifier, role_permission_in)
