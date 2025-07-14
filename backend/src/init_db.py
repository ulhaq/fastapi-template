import asyncio
import logging
import logging.config
import os
import sys

from alembic import command
from alembic.config import Config
from src.core.database import AsyncSessionLocal
from src.core.logging import LOGGING_CONFIG
from src.core.security import hash_password
from src.models.permission import Permission
from src.models.role import Role
from src.models.user import User

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger(__name__)


alembic_cfg = Config(os.getcwd() + "/alembic.ini")

INIT_AUTH_DATA: dict = {
    "permissions": [
        {
            "name": "read_user",
            "description": "Allows the user to read user accounts.",
        },
        {
            "name": "create_user",
            "description": "Allows the user to create new user accounts.",
        },
        {
            "name": "update_user",
            "description": "Allows the user to update user accounts.",
        },
        {
            "name": "delete_user",
            "description": "Allows the user to delete user accounts.",
        },
        {
            "name": "read_role",
            "description": "Allows the user to read roles.",
        },
        {
            "name": "create_role",
            "description": "Allows the user to create new roles.",
        },
        {
            "name": "update_role",
            "description": "Allows the user to update roles.",
        },
        {
            "name": "delete_role",
            "description": "Allows the user to delete roles.",
        },
        {
            "name": "manage_user_role",
            "description": "Allows the user to manage users' roles.",
        },
        {
            "name": "read_permission",
            "description": "Allows the user to read permissions.",
        },
        {
            "name": "create_permission",
            "description": "Allows the user to create new permissions.",
        },
        {
            "name": "update_permission",
            "description": "Allows the user to update permissions.",
        },
        {
            "name": "delete_permission",
            "description": "Allows the user to delete permissions.",
        },
        {
            "name": "manage_role_permission",
            "description": "Allows the user to manage roles' permissions.",
        },
    ],
    "roles": [
        {
            "name": "admin",
            "description": "Full access to all system features and settings.",
            "permissions": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
        },
        {
            "name": "standard",
            "description": "Access to manage and view own resources.",
            "permissions": [1, 2],
        },
    ],
    "users": [
        {
            "name": "Admin",
            "email": "admin@example.org",
            "password": "password",
            "roles": [1],
        },
        {
            "name": "Standard",
            "email": "standard@example.org",
            "password": "password",
            "roles": [2],
        },
        {
            "name": "No Roles",
            "email": "no_roles@example.org",
            "password": "password",
            "roles": [],
        },
    ],
}


async def up() -> None:
    command.upgrade(alembic_cfg, "head")

    async with AsyncSessionLocal() as session:
        permissions = []
        for permission in INIT_AUTH_DATA["permissions"]:
            _permission = Permission(
                name=permission["name"], description=permission["description"]
            )
            permissions.append(_permission)
        session.add_all(permissions)

        roles = []
        for role in INIT_AUTH_DATA["roles"]:
            _role = Role(
                name=role["name"],
                description=role["description"],
                permissions=[
                    permission
                    for idx, permission in enumerate(permissions, 1)
                    if idx in role["permissions"]
                ],
            )
            roles.append(_role)
        session.add_all(roles)

        users = []
        for user in INIT_AUTH_DATA["users"]:
            _user = User(
                name=user["name"],
                email=user["email"],
                password=hash_password(user["password"]),
                roles=[
                    role for idx, role in enumerate(roles, 1) if idx in user["roles"]
                ],
            )
            users.append(_user)
        session.add_all(users)

        await session.commit()


async def main(drop: bool = False) -> None:
    if not drop:
        log.info("Creating tables and initial data")
        await up()
        log.info("Created tables and initial data")
    else:
        log.info("Dropping tables")
        command.downgrade(alembic_cfg, "base")
        log.info("Dropped tables")


if __name__ == "__main__":
    asyncio.run(main(drop="drop" in sys.argv))
