from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import require_owner, require_permission
from src.core.security import Auth
from src.enums import Permission
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.organization import (
    OrganizationBase,
    OrganizationOut,
    OrganizationPatch,
    TransferOwnershipIn,
)
from src.schemas.user import UserOut
from src.services.organization import OrganizationService

# pylint: disable=too-many-arguments

router = APIRouter(prefix="/organizations")


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_organizations(
    service: Annotated[OrganizationService, Depends()],
) -> list[OrganizationOut]:
    return await service.get_all_organizations()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_an_organization(
    service: Annotated[OrganizationService, Depends()],
    organization_in: OrganizationBase,
) -> OrganizationOut:
    return await service.create_organization(organization_in)


@router.patch("/{identifier}", status_code=status.HTTP_200_OK)
async def patch_an_organization(
    service: Annotated[OrganizationService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.UPDATE_ORGANIZATION))],
    identifier: Annotated[int, Path()],
    organization_in: OrganizationPatch,
) -> OrganizationOut:
    return await service.patch_organization(identifier, organization_in)


@router.get("/{identifier}", status_code=status.HTTP_200_OK)
async def retrieve_an_organization(
    service: Annotated[OrganizationService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_ORGANIZATION))],
    identifier: Annotated[int, Path()],
) -> OrganizationOut:
    return await service.get_organization(identifier)


@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_an_organization(
    service: Annotated[OrganizationService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.DELETE_ORGANIZATION))],
    identifier: Annotated[int, Path()],
) -> None:
    await service.delete_organization(identifier)


@router.post(
    "/{organization_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def add_user_to_organization(
    service: Annotated[OrganizationService, Depends()],
    _: Annotated[
        Auth, Depends(require_permission(Permission.MANAGE_ORGANIZATION_USER))
    ],
    organization_id: Annotated[int, Path()],
    user_id: Annotated[int, Path()],
) -> None:
    await service.add_user_to_organization(organization_id, user_id)


@router.delete(
    "/{organization_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_user_from_organization(
    service: Annotated[OrganizationService, Depends()],
    _: Annotated[
        Auth, Depends(require_permission(Permission.MANAGE_ORGANIZATION_USER))
    ],
    organization_id: Annotated[int, Path()],
    user_id: Annotated[int, Path()],
) -> None:
    await service.remove_user_from_organization(organization_id, user_id)


@router.post(
    "/{organization_id}/transfer-ownership", status_code=status.HTTP_204_NO_CONTENT
)
async def transfer_organization_ownership(
    service: Annotated[OrganizationService, Depends()],
    _: Annotated[Auth, Depends(require_owner())],
    organization_id: Annotated[int, Path()],
    schema_in: TransferOwnershipIn,
) -> None:
    await service.transfer_ownership(organization_id, schema_in)


@router.get("/{organization_id}/users", status_code=status.HTTP_200_OK)
async def get_organization_users(
    *,
    service: Annotated[OrganizationService, Depends()],
    _: Annotated[Auth, Depends(require_permission(Permission.READ_USER))],
    organization_id: Annotated[int, Path()],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[UserOut]:
    return await service.get_organization_users(
        organization_id,
        PageQueryParams(
            sort=sort, filters=filters, page_size=page_size, page_number=page_number
        ),
    )
