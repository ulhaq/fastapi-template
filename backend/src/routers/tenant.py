from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import require_permission
from src.core.security import Auth
from src.enums import Permission
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.tenant import TenantBase, TenantOut, TenantPatch
from src.schemas.user import UserOut
from src.services.tenant import TenantService

# pylint: disable=too-many-arguments

router = APIRouter(prefix="/tenants")


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_tenants(
    service: Annotated[TenantService, Depends()],
) -> list[TenantOut]:
    return await service.get_all_tenants()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_a_tenant(
    service: Annotated[TenantService, Depends()],
    tenant_in: TenantBase,
) -> TenantOut:
    return await service.create_tenant(tenant_in)


@router.patch("/{identifier}", status_code=status.HTTP_200_OK)
async def patch_a_tenant(
    service: Annotated[TenantService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.UPDATE_TENANT))],
    identifier: Annotated[int, Path()],
    tenant_in: TenantPatch,
) -> TenantOut:
    return await service.patch_tenant(identifier, tenant_in)


@router.get("/{identifier}", status_code=status.HTTP_200_OK)
async def retrieve_a_tenant(
    service: Annotated[TenantService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_TENANT))],
    identifier: Annotated[int, Path()],
) -> TenantOut:
    return await service.get_tenant(identifier)


@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_tenant(
    service: Annotated[TenantService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.DELETE_TENANT))],
    identifier: Annotated[int, Path()],
) -> None:
    await service.delete_tenant(identifier)


# TODO: can be removed?
@router.post("/{tenant_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_user_to_tenant(
    service: Annotated[TenantService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.MANAGE_TENANT_USER))],
    tenant_id: Annotated[int, Path()],
    user_id: Annotated[int, Path()],
) -> None:
    await service.add_user_to_tenant(tenant_id, user_id)


# TODO: can be removed?
@router.delete("/{tenant_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_tenant(
    service: Annotated[TenantService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.MANAGE_TENANT_USER))],
    tenant_id: Annotated[int, Path()],
    user_id: Annotated[int, Path()],
) -> None:
    await service.remove_user_from_tenant(tenant_id, user_id)


@router.get("/{tenant_id}/users", status_code=status.HTTP_200_OK)
async def get_tenant_users(
    *,
    service: Annotated[TenantService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_USER))],
    tenant_id: Annotated[int, Path()],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[UserOut]:
    return await service.get_tenant_users(
        tenant_id,
        PageQueryParams(
            sort=sort, filters=filters, page_size=page_size, page_number=page_number
        ),
    )
