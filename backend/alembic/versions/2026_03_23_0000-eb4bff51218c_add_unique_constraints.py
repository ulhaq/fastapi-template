"""add_unique_constraints

Revision ID: eb4bff51218c
Revises: 6a1fe3e715b9
Create Date: 2026-03-23 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "eb4bff51218c"
down_revision: Union[str, None] = "6a1fe3e715b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_role_name", table_name="role")
    op.create_index("ix_role_name", "role", ["name"], unique=True)

    op.drop_index("ix_permission_name", table_name="permission")
    op.create_index("ix_permission_name", "permission", ["name"], unique=True)

    op.create_unique_constraint("uq_user_role", "user_role", ["user_id", "role_id"])
    op.create_unique_constraint(
        "uq_role_permission", "role_permission", ["role_id", "permission_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_role_permission", "role_permission", type_="unique")
    op.drop_constraint("uq_user_role", "user_role", type_="unique")

    op.drop_index("ix_permission_name", table_name="permission")
    op.create_index("ix_permission_name", "permission", ["name"], unique=False)

    op.drop_index("ix_role_name", table_name="role")
    op.create_index("ix_role_name", "role", ["name"], unique=False)
