"""add_token_tables

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-04-05 00:01:00.000000

"""

from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.enums import PERMISSION_DESCRIPTIONS, Permission

_API_TOKEN_PERMISSION = Permission.MANAGE_API_TOKEN

_permission_table = sa.table(
    "permission",
    sa.Column("name", sa.String),
    sa.Column("description", sa.String),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
)

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "api_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("token_prefix", sa.String(), nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            default=datetime.now(UTC),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            default=datetime.now(UTC),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organization.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_api_token_token_hash"), "api_token", ["token_hash"], unique=True
    )
    op.create_index(op.f("ix_api_token_user_id"), "api_token", ["user_id"])
    op.create_index(op.f("ix_api_token_organization_id"), "api_token", ["organization_id"])

    op.create_table(
        "invite_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            default=datetime.now(UTC),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        op.f("ix_invite_token_email"),
        "invite_token",
        ["email"],
        unique=True,
    )

    op.create_table(
        "email_verification_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("token", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            default=datetime.now(UTC),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        op.f("ix_email_verification_token_email"),
        "email_verification_token",
        ["email"],
        unique=True,
    )


    now = datetime.now(UTC)
    op.bulk_insert(
        _permission_table,
        [
            {
                "name": _API_TOKEN_PERMISSION.value,
                "description": PERMISSION_DESCRIPTIONS[_API_TOKEN_PERMISSION],
                "created_at": now,
                "updated_at": now,
            }
        ],
    )

    conn = op.get_bind()
    roles = conn.execute(
        sa.text("SELECT id FROM role WHERE name IN ('Admin', 'Member')")
    ).fetchall()
    perm = conn.execute(
        sa.text("SELECT id FROM permission WHERE name = :name"),
        {"name": _API_TOKEN_PERMISSION.value},
    ).fetchone()
    if perm:
        for role in roles:
            conn.execute(
                sa.text(
                    "INSERT INTO role_permission (role_id, permission_id, created_at, updated_at)"
                    " VALUES (:r, :p, :now, :now) ON CONFLICT DO NOTHING"
                ),
                {"r": role.id, "p": perm.id, "now": now},
            )


def downgrade() -> None:
    conn = op.get_bind()
    perm = conn.execute(
        sa.text("SELECT id FROM permission WHERE name = :name"),
        {"name": _API_TOKEN_PERMISSION.value},
    ).fetchone()
    if perm:
        conn.execute(
            sa.text("DELETE FROM role_permission WHERE permission_id = :p"),
            {"p": perm.id},
        )
    op.execute(
        _permission_table.delete().where(
            _permission_table.c.name == _API_TOKEN_PERMISSION.value
        )
    )

    op.drop_index(
        op.f("ix_email_verification_token_email"),
        table_name="email_verification_token",
    )
    op.drop_table("email_verification_token")
    op.drop_index(op.f("ix_invite_token_email"), table_name="invite_token")
    op.drop_table("invite_token")
    op.drop_index(op.f("ix_api_token_organization_id"), table_name="api_token")
    op.drop_index(op.f("ix_api_token_user_id"), table_name="api_token")
    op.drop_index(op.f("ix_api_token_token_hash"), table_name="api_token")
    op.drop_table("api_token")
