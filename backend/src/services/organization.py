import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends

from src.billing.dependencies import BillingProviderDep
from src.core.context import client_ip_var
from src.core.dependencies import authenticate
from src.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    PermissionDeniedException,
)
from src.core.security import Auth
from src.enums import OWNER_ROLE_NAME, AuditAction, ErrorCode
from src.models.organization import Organization
from src.repositories.organization import OrganizationRepository
from src.repositories.repository_manager import RepositoryManager
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.organization import (
    MyOrganizationOut,
    OrganizationBase,
    OrganizationOut,
    OrganizationPatch,
    TransferOwnershipIn,
)
from src.schemas.user import UserOut
from src.services.base import ResourceService
from src.services.utils import setup_new_organization

log = logging.getLogger(__name__)


class OrganizationService(
    ResourceService[
        OrganizationRepository,
        Organization,
        OrganizationBase | OrganizationPatch,
        OrganizationOut,
    ]
):
    current_user: Auth

    def __init__(
        self,
        repos: Annotated[RepositoryManager, Depends()],
        current_user: Annotated[Auth, Depends(authenticate)],
        provider: BillingProviderDep,
    ) -> None:
        self.repo = repos.organization
        self.current_user = current_user
        self.provider = provider
        super().__init__(repos)

    async def get(self, identifier: int, include_deleted: bool = False) -> Organization:
        membership = await self.repos.user_organization.get_by_user_and_organization(
            self.current_user.id, identifier
        )
        if not membership:
            raise PermissionDeniedException(
                "You are not allowed to access other organizations"
            )
        return await super().get(identifier, include_deleted=include_deleted)

    async def paginate(
        self,
        schema_out: type[OrganizationOut],
        page_query_params: PageQueryParams,
        include_deleted: bool = False,
    ) -> PaginatedResponse[OrganizationOut]:
        return await super().paginate(
            schema_out=schema_out,
            page_query_params=page_query_params,
            include_deleted=include_deleted,
        )

    async def get_all_organizations(self) -> list[MyOrganizationOut]:
        memberships = await self.repos.user_organization.get_all_for_user(
            self.current_user.id
        )
        organization_ids = [m.organization_id for m in memberships]
        organizations = await self.repos.organization.filter_by_ids(organization_ids)
        organization_map = {o.id: o for o in organizations}
        user = await self.repos.user.get(self.current_user.id)
        owner_org_ids = {
            r.organization_id
            for r in (user.roles if user else [])
            if r.is_protected and r.name == OWNER_ROLE_NAME
        }
        return [
            MyOrganizationOut(
                **OrganizationOut.model_validate(organization_map[oid]).model_dump(),
                is_owner=oid in owner_org_ids,
            )
            for oid in organization_ids
            if oid in organization_map
        ]

    async def create_organization(self, schema_in: OrganizationBase) -> OrganizationOut:
        existing = await self.repo.get_one_by_name(schema_in.name, include_deleted=True)
        if existing is not None and existing.deleted_at is None:
            raise AlreadyExistsException(
                f"Organization already exists. [name={schema_in.name}]"
            )

        if existing is not None and existing.deleted_at is not None:
            organization = await self.repo.restore(existing)
        else:
            organization = await self.repo.create(name=schema_in.name)

        await self.repos.user_organization.create(
            user_id=self.current_user.id,
            organization_id=organization.id,
            last_active_at=datetime.now(UTC),
        )

        user = await self.repos.user.get_one(self.current_user.id)
        await setup_new_organization(self.repos, organization, user)

        return OrganizationOut.model_validate(organization)

    async def patch_organization(
        self, identifier: int, schema_in: OrganizationPatch
    ) -> OrganizationOut:
        if identifier != self.current_user.organization_id:
            raise PermissionDeniedException(
                "You can only update your active organization"
            )

        async def validate() -> None:
            if schema_in.name:
                existing_org = await self.repo.get_one_by_name(schema_in.name)
                if existing_org and existing_org.id != identifier:
                    raise AlreadyExistsException(
                        f"Organization already exists. [name={schema_in.name}]"
                    )

        updated = await super().patch(identifier, schema_in, validate)
        await self.repos.audit_log.create(
            action=AuditAction.ORG_UPDATE,
            organization_id=self.current_user.organization_id,
            user_id=self.current_user.id,
            resource_type="organization",
            resource_id=identifier,
            ip_address=client_ip_var.get(),
        )
        return OrganizationOut.model_validate(updated)

    async def get_organization(self, identifier: int) -> OrganizationOut:
        return OrganizationOut.model_validate(await self.get(identifier))

    async def delete_organization(
        self, identifier: int, force_delete: bool = False
    ) -> None:
        if identifier != self.current_user.organization_id:
            raise PermissionDeniedException(
                "You can only delete your active organization"
            )

        subscription = await self.repos.subscription.get_active_for_organization(
            identifier
        )
        if subscription and subscription.external_subscription_id:
            raise PermissionDeniedException(
                "Cannot delete an organization with an active subscription."
                " Cancel the subscription first.",
                error_code=ErrorCode.SUBSCRIPTION_ALREADY_ACTIVE,
            )

        # Load members before deletion so the DB cascade hasn't removed the rows yet
        memberships = (
            await self.repos.user_organization.get_all_members_of_organization(
                identifier
            )
        )
        for membership in memberships:
            user = await self.repos.user.get(membership.user_id)
            if not user:
                continue
            # get_all_for_user filters soft-deleted orgs
            # so this gives remaining active orgs
            other = await self.repos.user_organization.get_all_for_user(
                membership.user_id
            )
            if not any(m.organization_id != identifier for m in other):
                await self.repos.refresh_token.delete_by_user(user)
                await self.repos.user.delete(user)

        await super().delete(identifier, force_delete=force_delete)

    async def get_organization_users(
        self, organization_id: int, page_query_params: PageQueryParams
    ) -> PaginatedResponse[UserOut]:
        await self.get(organization_id)  # validates access

        self.repos.user.set_organization_scope(organization_id)
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
                        role
                        for role in user.roles
                        if role.organization_id == organization_id
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

    async def transfer_ownership(
        self, organization_id: int, schema_in: TransferOwnershipIn
    ) -> None:
        if organization_id != self.current_user.organization_id:
            raise PermissionDeniedException(
                "You can only transfer ownership of your active organization"
            )

        if schema_in.user_id == self.current_user.id:
            raise PermissionDeniedException("Cannot transfer ownership to yourself")

        organization = await self.get(organization_id)

        membership = await self.repos.user_organization.get_by_user_and_organization(
            schema_in.user_id, organization_id
        )
        if not membership:
            raise NotFoundException("Target user is not a member of this organization")

        self.repos.role.set_organization_scope(organization_id)
        owner_role = await self.repos.role.get_one_by_name(OWNER_ROLE_NAME)
        if not owner_role:
            raise NotFoundException("Owner role not found")

        current_owner = await self.repos.user.get_one(self.current_user.id)
        new_owner = await self.repos.user.get_one(schema_in.user_id)

        await self.repos.user.remove_roles(current_owner, owner_role.id)
        await self.repos.user.add_roles(new_owner, owner_role.id)

        if organization.external_customer_id:
            await self.provider.update_customer(
                organization.external_customer_id, email=new_owner.email
            )
