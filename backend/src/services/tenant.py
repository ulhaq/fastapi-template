import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends

from src.billing.abc import BillingProviderABC
from src.billing.dependencies import BillingProviderDep
from src.core.dependencies import authenticate
from src.core.exceptions import (
    AlreadyExistsException,
    BillingProviderException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import Auth
from src.enums import OWNER_ROLE_NAME, Permission
from src.models.tenant import Tenant
from src.models.user import User
from src.repositories.repository_manager import RepositoryManager
from src.repositories.tenant import TenantRepository
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.tenant import TenantBase, TenantOut, TenantPatch
from src.schemas.user import UserOut
from src.services.base import ResourceService

log = logging.getLogger(__name__)


async def _setup_new_tenant(
    repos: RepositoryManager,
    provider: BillingProviderABC,
    tenant: Tenant,
    user: User,
    user_email: str,
) -> None:
    permissions = await repos.permission.get_all()
    owner_role = await repos.role.create(
        name=OWNER_ROLE_NAME,
        description="Full access to all system features and settings.",
        is_protected=True,
        tenant=tenant,
    )
    await repos.role.add_permissions(owner_role, *[p.id for p in permissions])
    await repos.user.add_roles(user, owner_role.id)

    highest_price = await repos.plan_price.get_highest_price()
    if highest_price and highest_price.external_price_id:
        try:
            external_customer_id = await provider.get_or_create_customer(
                tenant_id=tenant.id,
                tenant_name=tenant.name,
                email=user_email,
            )
            await repos.tenant.update(tenant, external_customer_id=external_customer_id)
            # Create an incomplete subscription row. The user must complete
            # Stripe Checkout (which collects billing address and optional
            # VAT ID) to start the trial - no credit card is required.
            await repos.subscription.create(
                tenant_id=tenant.id,
                plan_price_id=highest_price.id,
                status="incomplete",
            )
        except BillingProviderException as exc:
            log.warning(
                "Trial plan billing setup failed for tenant %s (non-fatal): %s",
                tenant.id,
                exc,
            )
    else:
        log.warning(
            "No active plan found - skipping auto-subscription for tenant %s",
            tenant.id,
        )


class TenantService(
    ResourceService[TenantRepository, Tenant, TenantBase | TenantPatch, TenantOut]
):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
        provider: BillingProviderDep,
    ) -> None:
        self.repo = repos.tenant
        self.current_user = current_user
        self.provider = provider
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
        return await super().paginate(
            schema_out=schema_out,
            page_query_params=page_query_params,
            include_deleted=include_deleted,
        )

    async def get_all_tenants(self) -> list[TenantOut]:
        memberships = await self.repos.user_tenant.get_all_for_user(
            self.current_user.id
        )
        tenant_ids = [m.tenant_id for m in memberships]
        tenants = await self.repos.tenant.filter_by_ids(tenant_ids)
        tenant_map = {t.id: t for t in tenants}
        return [
            TenantOut.model_validate(tenant_map[tid])
            for tid in tenant_ids
            if tid in tenant_map
        ]

    async def create_tenant(self, schema_in: TenantBase) -> TenantOut:
        existing = await self.repo.get_one_by_name(schema_in.name, include_deleted=True)
        if existing is not None and existing.deleted_at is None:
            raise AlreadyExistsException(
                f"Tenant already exists. [name={schema_in.name}]"
            )

        if existing is not None and existing.deleted_at is not None:
            tenant = await self.repo.restore(existing)
        else:
            tenant = await self.repo.create(name=schema_in.name)

        await self.repos.user_tenant.create(
            user_id=self.current_user.id,
            tenant_id=tenant.id,
            last_active_at=datetime.now(UTC),
        )

        user = await self.repos.user.get_one(self.current_user.id)
        await _setup_new_tenant(
            self.repos, self.provider, tenant, user, self.current_user.email
        )

        return TenantOut.model_validate(tenant)

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

    async def get_tenant_users(
        self, tenant_id: int, page_query_params: PageQueryParams
    ) -> PaginatedResponse[UserOut]:
        await self.get(tenant_id)  # validates access

        self.repos.user.set_tenant_scope(tenant_id)
        items, total = await self.repos.user.paginate(
            sort=page_query_params.sort,
            filters=page_query_params.filters,
            page_size=page_query_params.page_size,
            page_number=page_query_params.page_number,
        )
        result = [
            UserOut.model_validate(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "created_at": user.created_at,
                    "updated_at": user.updated_at,
                    "roles": [
                        role for role in user.roles if role.tenant_id == tenant_id
                    ],
                }
            )
            for user in items
        ]
        return PaginatedResponse(
            items=result,
            page_number=page_query_params.page_number,
            page_size=page_query_params.page_size,
            total=total,
        )
