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
from src.enums import OWNER_ROLE_NAME, Permission
from src.models.permission import Permission as PermissionModel
from src.models.role import Role
from src.models.tenant import Tenant
from src.models.user import User
from src.models.user_tenant import UserTenant

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger(__name__)


alembic_cfg = Config(os.getcwd() + "/alembic.ini")

INIT_AUTH_DATA: dict = {
    "tenants": [
        {"name": "Tenant 1"},
        {"name": "Tenant 2"},
    ],
    "roles": [
        {
            "name": OWNER_ROLE_NAME,
            "description": "Full access to all system features and settings.",
            "permissions": list(Permission),
            "tenant": 1,
            "is_protected": True,
        },
        {
            "name": "standard",
            "description": "Access to manage and view own resources.",
            "permissions": [Permission.READ_USER, Permission.CREATE_USER],
            "tenant": 1,
        },
        {
            "name": OWNER_ROLE_NAME,
            "description": "Full access to all system features and settings.",
            "permissions": list(Permission),
            "tenant": 2,
            "is_protected": True,
        },
        {
            "name": "standard",
            "description": "Access to manage and view own resources.",
            "permissions": [Permission.READ_USER, Permission.CREATE_USER],
            "tenant": 2,
        },
    ],
    "users": [
        {
            "name": "Admin",
            "email": "admin@example.org",
            "password": "password",
            "tenant": 1,
            "roles": [1],
        },
        {
            "name": "Standard",
            "email": "standard@example.org",
            "password": "password",
            "tenant": 1,
            "roles": [2],
        },
        {
            "name": "No Roles",
            "email": "no_roles@example.org",
            "password": "password",
            "tenant": 1,
            "roles": [],
        },
        {
            "name": "Admin 2",
            "email": "admin2@example.org",
            "password": "password",
            "tenant": 2,
            "roles": [3],
        },
    ],
}


async def up() -> None:
    upgrade(alembic_cfg, "head")

    async with ASYNC_SESSION_LOCAL() as session:
        tenants = []
        for tenant in INIT_AUTH_DATA["tenants"]:
            tenants.append(Tenant(name=tenant["name"]))
        session.add_all(tenants)

        rs = await session.execute(select(PermissionModel))
        permissions = list(rs.scalars().all())

        roles = []
        for role in INIT_AUTH_DATA["roles"]:
            roles.append(
                Role(
                    name=role["name"],
                    description=role["description"],
                    is_protected=role.get("is_protected", False),
                    tenant=tenants[role["tenant"] - 1],
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

        user_tenants = []
        for user_data, user in zip(INIT_AUTH_DATA["users"], users):
            user_tenants.append(
                UserTenant(
                    user_id=user.id,
                    tenant_id=tenants[user_data["tenant"] - 1].id,
                    last_active_at=datetime.now(UTC),
                )
            )
        session.add_all(user_tenants)

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
