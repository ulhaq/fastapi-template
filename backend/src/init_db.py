import asyncio
import logging
import logging.config
import os
import sys

from alembic.command import downgrade, upgrade
from alembic.config import Config

from src.core.logging import LOGGING_CONFIG
from src.enums import OWNER_ROLE_NAME, Permission

logging.config.dictConfig(LOGGING_CONFIG)
log = logging.getLogger(__name__)


alembic_cfg = Config(os.getcwd() + "/alembic.ini")

INIT_AUTH_DATA: dict = {
    "organizations": [
        {"name": "Organization 1"},
        {"name": "Organization 2"},
    ],
    "roles": [
        {
            "name": OWNER_ROLE_NAME,
            "description": "Full access to all system features and settings.",
            "permissions": list(Permission),
            "organization": 1,
            "is_protected": True,
        },
        {
            "name": "standard",
            "description": "Access to manage and view own resources.",
            "permissions": [Permission.READ_USER, Permission.CREATE_USER],
            "organization": 1,
        },
        {
            "name": OWNER_ROLE_NAME,
            "description": "Full access to all system features and settings.",
            "permissions": list(Permission),
            "organization": 2,
            "is_protected": True,
        },
        {
            "name": "standard",
            "description": "Access to manage and view own resources.",
            "permissions": [Permission.READ_USER, Permission.CREATE_USER],
            "organization": 2,
        },
    ],
    "users": [
        {
            "name": "Admin",
            "email": "admin@example.org",
            "password": "password",
            "organization": 1,
            "roles": [1],
        },
        {
            "name": "Standard",
            "email": "standard@example.org",
            "password": "password",
            "organization": 1,
            "roles": [2],
        },
        {
            "name": "No Roles",
            "email": "no_roles@example.org",
            "password": "password",
            "organization": 1,
            "roles": [],
        },
        {
            "name": "Admin 2",
            "email": "admin2@example.org",
            "password": "password",
            "organization": 2,
            "roles": [3],
        },
    ],
}


async def up() -> None:
    upgrade(alembic_cfg, "head")

    # async with ASYNC_SESSION_LOCAL() as session:
    #     organizations = []
    #     for organization in INIT_AUTH_DATA["organizations"]:
    #         organizations.append(Organization(name=organization["name"]))
    #     session.add_all(organizations)

    #     rs = await session.execute(select(PermissionModel))
    #     permissions = list(rs.scalars().all())

    #     roles = []
    #     for role in INIT_AUTH_DATA["roles"]:
    #         roles.append(
    #             Role(
    #                 name=role["name"],
    #                 description=role["description"],
    #                 is_protected=role.get("is_protected", False),
    #                 organization=organizations[role["organization"] - 1],
    #                 permissions=[
    #                     permission
    #                     for permission in permissions
    #                     if permission.name in role["permissions"]
    #                 ],
    #             )
    #         )
    #     session.add_all(roles)

    #     users = []
    #     for user in INIT_AUTH_DATA["users"]:
    #         users.append(
    #             User(
    #                 name=user["name"],
    #                 email=user["email"],
    #                 password=hash_secret(user["password"]),
    #                 roles=[
    #                     role
    #                     for idx, role in enumerate(roles, 1)
    #                     if idx in user["roles"]
    #                 ],
    #             )
    #         )
    #     session.add_all(users)

    #     await session.flush()

    #     user_organizations = []
    #     for user_data, user in zip(INIT_AUTH_DATA["users"], users):
    #         user_organizations.append(
    #             Userorganization(
    #                 user_id=user.id,
    #                 organization_id=organizations[user_data["organization"] - 1].id,
    #                 last_active_at=datetime.now(UTC),
    #             )
    #         )
    #     session.add_all(user_organizations)

    #     await session.commit()


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
