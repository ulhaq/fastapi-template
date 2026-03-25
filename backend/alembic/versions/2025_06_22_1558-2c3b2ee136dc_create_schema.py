"""create schema

Revision ID: 2c3b2ee136dc
Revises:
Create Date: 2025-06-22 15:58:50.524796

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2c3b2ee136dc"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Standalone tables (no foreign keys)

    op.create_table(
        "tenant",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenant_name"), "tenant", ["name"])

    op.create_table(
        "permission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_permission_name"), "permission", ["name"], unique=True
    )

    # Tables with foreign keys to standalone tables

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name="fk_user_tenant_id_tenant",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_user_name"), "user", ["name"])

    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name="fk_role_tenant_id_tenant",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
    )
    op.create_index(op.f("ix_role_name"), "role", ["name"])

    # Junction tables

    op.create_table(
        "user_role",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    op.create_table(
        "role_permission",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["role_id"], ["role.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permission.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "role_id", "permission_id", name="uq_role_permission"
        ),
    )

    # Dependent tables

    op.create_table(
        "password_reset_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )

    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["user.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )


def downgrade() -> None:
    op.drop_table("refresh_token")
    op.drop_table("password_reset_token")
    op.drop_table("role_permission")
    op.drop_table("user_role")
    op.drop_index(op.f("ix_role_name"), table_name="role")
    op.drop_table("role")
    op.drop_index(op.f("ix_user_name"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_permission_name"), table_name="permission")
    op.drop_table("permission")
    op.drop_index(op.f("ix_tenant_name"), table_name="tenant")
    op.drop_table("tenant")
