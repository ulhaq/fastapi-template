import copy
from typing import Annotated

from fastapi import Depends

from src.core.dependencies import authenticate
from src.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import Auth
from src.enums import Permission
from src.models.tenant import Tenant
from src.repositories.repository_manager import RepositoryManager
from src.repositories.tenant import TenantRepository
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.tenant import TenantBase, TenantOut, TenantPatch
from src.schemas.user import UserOut
from src.services.base import ResourceService


class TenantService(
    ResourceService[TenantRepository, Tenant, TenantBase | TenantPatch, TenantOut]
):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
    ) -> None:
        self.repo = repos.tenant
        self.current_user = current_user
        super().__init__(repos)

    async def get(self, identifier: int, include_deleted: bool = False) -> Tenant:
        membership = await self.repos.user_tenant.get_by_user_and_tenant(
            self.current_user.id, identifier
        )
        if not membership:
            raise PermissionDeniedException(
                "You are not allowed to access other tenants"
            )
        return await super().get(identifier, include_deleted=include_deleted)

    async def paginate(
        self,
        schema_out: type[TenantOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[TenantOut]:
        tenant = await self.get(
            self.current_user.tenant_id, include_deleted=include_deleted
        )
        items = (
            [schema_out.model_validate(tenant)]
            if page_query_params.page_number == 1
            else []
        )
        return PaginatedResponse(
            items=items,
            page_number=page_query_params.page_number,
            page_size=page_query_params.page_size,
            total=1,
        )

    async def create_tenant(self, schema_in: TenantBase) -> TenantOut:
        async def validate() -> None:
            if await self.repo.get_one_by_name(schema_in.name):
                raise AlreadyExistsException(
                    f"Tenant already exists. [name={schema_in.name}]"
                )

        return TenantOut.model_validate(await super().create(schema_in, validate))

    async def update_tenant(self, identifier: int, schema_in: TenantBase) -> TenantOut:
        async def validate() -> None:
            existing_tenant = await self.repo.get_one_by_name(schema_in.name)

            if existing_tenant and existing_tenant.id != identifier:
                raise AlreadyExistsException(
                    f"Tenant already exists. [name={schema_in.name}]"
                )

        return TenantOut.model_validate(
            await super().update(identifier, schema_in, validate)
        )

    async def patch_tenant(self, identifier: int, schema_in: TenantPatch) -> TenantOut:
        async def validate() -> None:
            if schema_in.name:
                existing_tenant = await self.repo.get_one_by_name(schema_in.name)
                if existing_tenant and existing_tenant.id != identifier:
                    raise AlreadyExistsException(
                        f"Tenant already exists. [name={schema_in.name}]"
                    )

        return TenantOut.model_validate(
            await super().patch(identifier, schema_in, validate)
        )

    async def get_tenant(self, identifier: int) -> TenantOut:
        return TenantOut.model_validate(await self.get(identifier))

    async def delete_tenant(self, identifier: int, force_delete: bool = False) -> None:
        await super().delete(identifier, force_delete=force_delete)

    async def add_user_to_tenant(self, tenant_id: int, user_id: int) -> None:
        if tenant_id != self.current_user.tenant_id:
            raise PermissionDeniedException(
                "You can only manage users in your active tenant"
            )

        await self.get(tenant_id)  # validates tenant exists and caller has access

        user = await self.repos.user.get(user_id)
        if not user:
            raise NotFoundException(f"User not found. [user_id={user_id}]")

        existing = await self.repos.user_tenant.get_by_user_and_tenant(
            user_id, tenant_id
        )
        if existing:
            raise AlreadyExistsException("User is already a member of this tenant")

        await self.repos.user_tenant.create(
            user_id=user_id,
            tenant_id=tenant_id,
        )

    async def remove_user_from_tenant(self, tenant_id: int, user_id: int) -> None:
        if tenant_id != self.current_user.tenant_id:
            raise PermissionDeniedException(
                "You can only manage users in your active tenant"
            )

        membership = await self.repos.user_tenant.get_by_user_and_tenant(
            user_id, tenant_id
        )
        if not membership:
            raise NotFoundException("User is not a member of this tenant")

        user = await self.repos.user.get(user_id)
        if user:
            self.repos.user.set_tenant_scope(tenant_id)
            tenant_roles = [r for r in user.roles if r.tenant_id == tenant_id]
            user_permissions = {
                p.name for role in tenant_roles for p in role.permissions
            }
            if Permission.MANAGE_USER_ROLE.value in user_permissions:
                if not await self.repos.user.has_other_user_with_permission(
                    Permission.MANAGE_USER_ROLE.value, exclude_user_id=user_id
                ):
                    raise PermissionDeniedException(
                        "Cannot remove this user: tenant must retain at least one "
                        "user with role management access"
                    )

            # Invalidate refresh token if this was the user's active tenant
            active = await self.repos.user_tenant.get_active_tenant_for_user(user_id)
            if active and active.tenant_id == tenant_id:
                await self.repos.refresh_token.delete_by_user(user)

        await self.repos.user_tenant.force_delete(membership)

    async def get_tenant_users(self, tenant_id: int) -> list[UserOut]:
        await self.get(tenant_id)  # validates access

        self.repos.user.set_tenant_scope(tenant_id)
        users = await self.repos.user.get_all()
        result = []
        for user in users:
            tenant_roles = [r for r in user.roles if r.tenant_id == tenant_id]
            result.append(
                UserOut.model_validate(
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "created_at": user.created_at,
                        "updated_at": user.updated_at,
                        "roles": tenant_roles,
                    }
                )
            )
        return result
