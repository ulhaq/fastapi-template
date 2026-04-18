"""seed_permissions

Revision ID: a1b2c3d4e5f6
Revises: eb4bff51218c
Create Date: 2026-03-23 00:01:00.000000

"""

from datetime import UTC, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from src.enums import PERMISSION_DESCRIPTIONS, Permission

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "2c3b2ee136dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_PERMISSIONS = [
    Permission.READ_ORGANIZATION,
    Permission.UPDATE_ORGANIZATION,
    Permission.DELETE_ORGANIZATION,
    Permission.MANAGE_ORGANIZATION_USER,
    Permission.READ_USER,
    Permission.CREATE_USER,
    Permission.UPDATE_USER,
    Permission.DELETE_USER,
    Permission.READ_ROLE,
    Permission.CREATE_ROLE,
    Permission.UPDATE_ROLE,
    Permission.DELETE_ROLE,
    Permission.MANAGE_USER_ROLE,
    Permission.READ_PERMISSION,
    Permission.MANAGE_ROLE_PERMISSION,
]

permission_table = sa.table(
    "permission",
    sa.Column("name", sa.String),
    sa.Column("description", sa.String),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
)


def upgrade() -> None:
    now = datetime.now(UTC)

    op.bulk_insert(
        permission_table,
        [
            {
                "name": permission.value,
                "description": PERMISSION_DESCRIPTIONS[permission],
                "created_at": now,
                "updated_at": now,
            }
            for permission in _PERMISSIONS
        ],
    )


def downgrade() -> None:
    op.execute(
        permission_table.delete().where(
            permission_table.c.name.in_([permission.value for permission in _PERMISSIONS])
        )
    )
