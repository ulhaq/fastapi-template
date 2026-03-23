import asyncio
import logging
import logging.config
import os
import sys

from alembic.command import downgrade, upgrade
from alembic.config import Config

from src.core.database import ASYNC_SESSION_LOCAL
from src.core.logging import LOGGING_CONFIG
from src.core.security import hash_secret
from src.enums import Permission
from src.models.company import Company
from src.models.permission import Permission as PermissionModel
from src.models.role import Role
from src.models.user import User

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger(__name__)


alembic_cfg = Config(os.getcwd() + "/alembic.ini")

INIT_AUTH_DATA: dict = {
    "companies": [
        {
            "name": "Company 1",
        },
        {
            "name": "Company 2",
        },
    ],
    "permissions": [
        {
            "name": "read:company",
            "description": "Allows the user to read company accounts.",
        },
        {
            "name": "create:company",
            "description": "Allows the user to create new company accounts.",
        },
        {
            "name": "update:company",
            "description": "Allows the user to update company accounts.",
        },
        {
            "name": "delete:company",
            "description": "Allows the user to delete company accounts.",
        },
        {
            "name": "manage:company_user",
            "description": "Allows the user to manage companies' users.",
        },
        {
            "name": "read:user",
            "description": "Allows the user to read users.",
        },
        {
            "name": "create:user",
            "description": "Allows the user to create new users.",
        },
        {
            "name": "update:user",
            "description": "Allows the user to update users.",
        },
        {
            "name": "delete:user",
            "description": "Allows the user to delete users.",
        },
        {
            "name": "read:role",
            "description": "Allows the user to read roles.",
        },
        {
            "name": "create:role",
            "description": "Allows the user to create new roles.",
        },
        {
            "name": "update:role",
            "description": "Allows the user to update roles.",
        },
        {
            "name": "delete:role",
            "description": "Allows the user to delete roles.",
        },
        {
            "name": "manage:user_role",
            "description": "Allows the user to manage users' roles.",
        },
        {
            "name": "read:permission",
            "description": "Allows the user to read permissions.",
        },
        {
            "name": "create:permission",
            "description": "Allows the user to create new permissions.",
        },
        {
            "name": "update:permission",
            "description": "Allows the user to update permissions.",
        },
        {
            "name": "delete:permission",
            "description": "Allows the user to delete permissions.",
        },
        {
            "name": "manage:role_permission",
            "description": "Allows the user to manage roles' permissions.",
        },
    ],
    "roles": [
        {
            "name": "admin",
            "description": "Full access to all system features and settings.",
            "permissions": list(Permission),
        },
        {
            "name": "standard",
            "description": "Access to manage and view own resources.",
            "permissions": [Permission.READ_USER, Permission.CREATE_USER],
        },
    ],
    "users": [
        {
            "name": "Admin",
            "email": "admin@example.org",
            "password": "password",
            "company": 1,
            "roles": [1],
        },
        {
            "name": "Standard",
            "email": "standard@example.org",
            "password": "password",
            "company": 2,
            "roles": [2],
        },
        {
            "name": "No Roles",
            "email": "no_roles@example.org",
            "password": "password",
            "company": 1,
            "roles": [],
        },
    ],
}


async def up() -> None:
    upgrade(alembic_cfg, "head")

    async with ASYNC_SESSION_LOCAL() as session:
        companies = []
        for company in INIT_AUTH_DATA["companies"]:
            companies.append(Company(name=company["name"]))
        session.add_all(companies)

        permissions = []
        for permission in INIT_AUTH_DATA["permissions"]:
            permissions.append(
                PermissionModel(
                    name=permission["name"], description=permission["description"]
                )
            )
        session.add_all(permissions)

        roles = []
        for role in INIT_AUTH_DATA["roles"]:
            roles.append(
                Role(
                    name=role["name"],
                    description=role["description"],
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
                    company=companies[user["company"] - 1],
                    roles=[
                        role
                        for idx, role in enumerate(roles, 1)
                        if idx in user["roles"]
                    ],
                )
            )
        session.add_all(users)

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
