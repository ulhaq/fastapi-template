"""add_unique_constraints

Revision ID: eb4bff51218c
Revises: 6a1fe3e715b9
Create Date: 2026-03-23 00:00:00.000000

"""

from typing import Sequence, Union

from sqlalchemy import Column, Integer
from alembic import op

revision: str = "eb4bff51218c"
down_revision: Union[str, None] = "6a1fe3e715b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add company_id to role table
    op.add_column("role", Column("company_id", Integer(), nullable=False))
    op.create_foreign_key(
        "fk_role_company_id_company", "role", "company", ["company_id"], ["id"]
    )

    # Replace global unique index on role.name with compound unique constraint
    op.drop_index("ix_role_name", table_name="role")
    op.create_index("ix_role_name", "role", ["name"], unique=False)
    op.create_unique_constraint("uq_role_company_name", "role", ["company_id", "name"])

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

    op.drop_constraint("uq_role_company_name", "role", type_="unique")
    op.drop_index("ix_role_name", table_name="role")
    op.create_index("ix_role_name", "role", ["name"], unique=False)

    op.drop_constraint("fk_role_company_id_company", "role", type_="foreignkey")
    op.drop_column("role", "company_id")
