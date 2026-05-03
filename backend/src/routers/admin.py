from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, status

from src.core.dependencies import require_superadmin
from src.core.security import Auth
from src.enums import AuditAction
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.admin import (
    AddMemberIn,
    AdminOrganizationCreate,
    AdminOrganizationOut,
    AdminUserOut,
    OrgMemberOut,
)
from src.schemas.audit_log import AuditLogOut
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.organization import OrganizationOut, OrganizationPatch
from src.schemas.user import UserPatch
from src.services.admin import AdminService

router = APIRouter(prefix="/admin")


@router.post("/organizations", status_code=status.HTTP_201_CREATED)
async def create_organization(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    organization_in: AdminOrganizationCreate,
) -> OrganizationOut:
    return await service.create_organization(organization_in)


@router.get("/organizations", status_code=status.HTTP_200_OK)
async def list_organizations(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 20,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[AdminOrganizationOut]:
    return await service.list_organizations(
        PageQueryParams(
            sort=sort,
            filters=filters,
            page_size=page_size,
            page_number=page_number,
        )
    )


@router.patch("/organizations/{identifier}", status_code=status.HTTP_200_OK)
async def patch_organization(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
    organization_in: OrganizationPatch,
) -> OrganizationOut:
    return await service.patch_organization(identifier, organization_in)


@router.delete("/organizations/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
) -> None:
    await service.delete_organization(identifier)


@router.get("/organizations/{identifier}/members", status_code=status.HTTP_200_OK)
async def list_org_members(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
) -> list[OrgMemberOut]:
    return await service.list_org_members(identifier)


@router.post("/organizations/{identifier}/members", status_code=status.HTTP_201_CREATED)
async def add_org_member(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
    member_in: AddMemberIn,
) -> OrgMemberOut:
    return await service.add_org_member(identifier, member_in)


@router.delete(
    "/organizations/{identifier}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_org_member(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
    user_id: Annotated[int, Path()],
) -> None:
    await service.remove_org_member(identifier, user_id)


@router.get("/users", status_code=status.HTTP_200_OK)
async def list_users(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 20,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[AdminUserOut]:
    return await service.list_users(
        PageQueryParams(
            sort=sort,
            filters=filters,
            page_size=page_size,
            page_number=page_number,
        )
    )


@router.patch("/users/{identifier}", status_code=status.HTTP_200_OK)
async def patch_user(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
    user_in: UserPatch,
) -> AdminUserOut:
    return await service.patch_user(identifier, user_in)


@router.delete("/users/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
) -> None:
    await service.delete_user(identifier)


@router.post(
    "/users/{identifier}/force-password-reset",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def force_password_reset(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    identifier: Annotated[int, Path()],
    background_tasks: BackgroundTasks,
) -> None:
    await service.force_password_reset(identifier, background_tasks.add_task)


@router.get("/audit-logs", status_code=status.HTTP_200_OK)
async def list_audit_logs(
    service: Annotated[AdminService, Depends()],
    _: Annotated[Auth, Depends(require_superadmin())],
    page_size: PageSizeQuery = 25,
    page_number: PageNumberQuery = 1,
    action: Annotated[
        AuditAction | None, Query(description="Filter by action type")
    ] = None,
) -> PaginatedResponse[AuditLogOut]:
    return await service.list_audit_logs(
        page_size=page_size,
        page_number=page_number,
        action_filter=action,
    )
