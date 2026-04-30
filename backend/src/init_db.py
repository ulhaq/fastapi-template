import asyncio
import logging
import logging.config
import os
import sys
from datetime import UTC, datetime

from alembic.command import downgrade, upgrade
from alembic.config import Config
from sqlalchemy import select

from src.core.database import ASYNC_SESSION_LOCAL
from src.core.logging import LOGGING_CONFIG
from src.core.security import hash_secret
from src.enums import DEFAULT_ROLES, OWNER_ROLE_NAME, Permission, PlanFeature
from src.models.api_token import ApiToken  # noqa: F401
from src.models.billing import (
    Plan,
    PlanPrice,
    Subscription,
)
from src.models.billing import (
    PlanFeature as PlanFeatureModel,
)
from src.models.organization import Organization
from src.models.permission import Permission as PermissionModel
from src.models.role import Role
from src.models.user import User
from src.models.user_organization import UserOrganization

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger(__name__)


alembic_cfg = Config(os.getcwd() + "/alembic.ini")

_admin_name, _admin_desc, _admin_perms = DEFAULT_ROLES[0]
_member_name, _member_desc, _member_perms = DEFAULT_ROLES[1]

INIT_AUTH_DATA: dict = {
    "organizations": [
        {"name": "Acme Corp"},
        {"name": "Globex Ltd"},
    ],
    "roles": [
        # Org 1 - index 1
        {
            "name": OWNER_ROLE_NAME,
            "description": "Full access to all system features and settings.",
            "permissions": list(Permission),
            "organization": 1,
            "is_protected": True,
        },
        # Org 1 - index 2
        {
            "name": _admin_name,
            "description": _admin_desc,
            "permissions": _admin_perms,
            "organization": 1,
        },
        # Org 1 - index 3
        {
            "name": _member_name,
            "description": _member_desc,
            "permissions": _member_perms,
            "organization": 1,
        },
        # Org 2 - index 4
        {
            "name": OWNER_ROLE_NAME,
            "description": "Full access to all system features and settings.",
            "permissions": list(Permission),
            "organization": 2,
            "is_protected": True,
        },
        # Org 2 - index 5
        {
            "name": _admin_name,
            "description": _admin_desc,
            "permissions": _admin_perms,
            "organization": 2,
        },
        # Org 2 - index 6
        {
            "name": _member_name,
            "description": _member_desc,
            "permissions": _member_perms,
            "organization": 2,
        },
    ],
    "users": [
        {
            "name": "Alice Owner",
            "email": "admin@example.org",
            "password": "password",
            "organization": 1,
            "roles": [1],
        },
        {
            "name": "Bob Member",
            "email": "standard@example.org",
            "password": "password",
            "organization": 1,
            "roles": [3],
        },
        {
            "name": "Carol (No Roles)",
            "email": "no_roles@example.org",
            "password": "password",
            "organization": 1,
            "roles": [],
        },
        {
            "name": "Dave Owner",
            "email": "admin2@example.org",
            "password": "password",
            "organization": 2,
            "roles": [4],
        },
    ],
}


async def up() -> None:
    upgrade(alembic_cfg, "head")

    async with ASYNC_SESSION_LOCAL() as session:
        organizations = []
        for organization in INIT_AUTH_DATA["organizations"]:
            organizations.append(Organization(name=organization["name"]))
        session.add_all(organizations)

        result = await session.execute(select(PermissionModel))
        permissions = list(result.scalars().all())

        roles = []
        for role in INIT_AUTH_DATA["roles"]:
            roles.append(
                Role(
                    name=role["name"],
                    description=role["description"],
                    is_protected=role.get("is_protected", False),
                    organization=organizations[role["organization"] - 1],
                    permissions=[
                        permission
                        for permission in permissions
                        if permission.name in role["permissions"]
                    ],
                )
            )
        session.add_all(roles)

        users = []
        for user in INIT_AUTH_DATA["users"]:
            users.append(
                User(
                    name=user["name"],
                    email=user["email"],
                    password=hash_secret(user["password"]),
                    roles=[
                        role
                        for idx, role in enumerate(roles, 1)
                        if idx in user["roles"]
                    ],
                )
            )
        session.add_all(users)

        await session.flush()

        user_organizations = []
        for user_data, user in zip(INIT_AUTH_DATA["users"], users, strict=False):
            user_organizations.append(
                UserOrganization(
                    user_id=user.id,
                    organization_id=organizations[user_data["organization"] - 1].id,
                    last_active_at=datetime.now(UTC),
                )
            )
        session.add_all(user_organizations)

        result = await session.execute(select(Plan).where(Plan.name == "Free"))
        free_plan = result.scalars().one()

        session.add(
            PlanFeatureModel(plan_id=free_plan.id, feature=PlanFeature.API_ACCESS)
        )

        result = await session.execute(
            select(PlanPrice).where(PlanPrice.plan_id == free_plan.id)
        )
        free_price = result.scalars().one()

        for organization in organizations:
            session.add(
                Subscription(
                    organization_id=organization.id,
                    plan_price_id=free_price.id,
                    status="active",
                )
            )

        await session.commit()


async def main(drop: bool = False) -> None:
    if not drop:
        log.info("Creating tables and initial data")
        await up()
        log.info("Created tables and initial data")
    else:
        log.info("Dropping tables")
        downgrade(alembic_cfg, "base")
        log.info("Dropped tables")


if __name__ == "__main__":
    asyncio.run(main(drop="drop" in sys.argv))
