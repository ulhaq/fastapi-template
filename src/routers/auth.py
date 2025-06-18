from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi.security import OAuth2PasswordRequestForm

from src.core.dependencies import authenticate
from src.core.security import Token
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.auth import (
    PermissionIn,
    PermissionOut,
    RoleIn,
    RoleOut,
    RolePermissionIn,
)
from src.schemas.common import Filters, PaginatedResponse
from src.schemas.user import UserIn, UserOut
from src.services.auth import AuthService, PermissionService, RoleService

auth_router = APIRouter()


@auth_router.post("/auth/register", status_code=201, response_model=UserOut)
async def create_an_account(
    service: Annotated[AuthService, Depends()], user_in: UserIn
):
    return await service.register_user(user_in)


@auth_router.post("/auth/token", status_code=200)
async def get_access_token(
    auth_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: Annotated[AuthService, Depends()],
) -> Token:
    return await service.get_access_token(auth_data)


role_router = APIRouter()


@role_router.get("/roles", dependencies=[Depends(authenticate)], status_code=200)
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


@role_router.post(
    "/roles",
    dependencies=[Depends(authenticate)],
    status_code=201,
    response_model=RoleOut,
)
async def create_a_role(service: Annotated[RoleService, Depends()], role_in: RoleIn):
    return await service.create_role(role_in)


@role_router.put(
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


@role_router.get(
    "/roles/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=RoleOut,
)
async def retrieve_a_role(
    service: Annotated[RoleService, Depends()], identifier: Annotated[int, Path()]
):
    return await service.get(identifier)


@role_router.delete(
    "/roles/{identifier}", dependencies=[Depends(authenticate)], status_code=204
)
async def delete_a_role(
    service: Annotated[RoleService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete(identifier)


@role_router.post(
    "/roles/{identifier}/permissions",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=RoleOut,
)
async def add_permissions_to_a_role(
    service: Annotated[RoleService, Depends()],
    identifier: Annotated[int, Path()],
    role_permission_in: RolePermissionIn,
):
    return await service.add_permissions(identifier, role_permission_in)


@role_router.delete(
    "/roles/{identifier}/permissions",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=RoleOut,
)
async def remove_permissions_from_a_role(
    service: Annotated[RoleService, Depends()],
    identifier: Annotated[int, Path()],
    role_permission_in: RolePermissionIn,
):
    return await service.remove_permissions(identifier, role_permission_in)


permission_router = APIRouter()


@permission_router.get(
    "/permissions", dependencies=[Depends(authenticate)], status_code=200
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
        sort=sort,
        filters=Filters.model_validate({"filters": filters}),
        page_size=page_size,
        page_number=page_number,
    )


@permission_router.post(
    "/permissions",
    dependencies=[Depends(authenticate)],
    status_code=201,
    response_model=PermissionOut,
)
async def create_a_permission(
    service: Annotated[PermissionService, Depends()], permission_in: PermissionIn
) -> PermissionOut:
    return await service.create_permission(permission_in)


@permission_router.put(
    "/permissions/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=PermissionOut,
)
async def update_a_permission(
    service: Annotated[PermissionService, Depends()],
    identifier: Annotated[int, Path()],
    permission_in: PermissionIn,
):
    return await service.update_permission(identifier, permission_in)


@permission_router.get(
    "/permissions/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=200,
    response_model=PermissionOut,
)
async def retrieve_a_permission(
    service: Annotated[PermissionService, Depends()], identifier: Annotated[int, Path()]
):
    return await service.get(identifier)


@permission_router.delete(
    "/permissions/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=204,
)
async def delete_a_permission(
    service: Annotated[PermissionService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete(identifier)
