"""add_billing_tables

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-29 00:01:00.000000

"""

from datetime import UTC, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.enums import PERMISSION_DESCRIPTIONS, Permission

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_PERMISSIONS = [
    Permission.READ_PLAN,
    Permission.READ_SUBSCRIPTION,
    Permission.MANAGE_SUBSCRIPTION,
]

permission_table = sa.table(
    "permission",
    sa.Column("name", sa.String),
    sa.Column("description", sa.String),
    sa.Column("created_at", sa.DateTime),
    sa.Column("updated_at", sa.DateTime),
)

_SUBSCRIPTION_STATUSES = ("incomplete", "incomplete_expired", "active", "trialing", "past_due", "canceled", "unpaid", "paused")



def upgrade() -> None:
    # --- tenant: add billing fields ---
    op.add_column("tenant", sa.Column("external_customer_id", sa.String, nullable=True))
    op.add_column(
        "tenant",
        sa.Column(
            "has_payment_method", sa.Boolean, nullable=False, server_default="0"
        ),
    )
    op.add_column(
        "tenant",
        sa.Column("trial_used", sa.Boolean, nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_tenant_external_customer_id",
        "tenant",
        ["external_customer_id"],
        unique=True,
    )

    # --- billing_plan ---
    op.create_table(
        "billing_plan",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("external_product_id", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("external_product_id", name="uq_billing_plan_external_product_id"),
    )
    op.create_index("ix_billing_plan_name", "billing_plan", ["name"])
    op.create_index(
        "ix_billing_plan_external_product_id",
        "billing_plan",
        ["external_product_id"],
    )

    # --- billing_plan_price ---
    op.create_table(
        "billing_plan_price",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "plan_id",
            sa.Integer,
            sa.ForeignKey("billing_plan.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("interval", sa.String, nullable=False),
        sa.Column("interval_count", sa.Integer, nullable=False, default=1),
        sa.Column("external_price_id", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("external_price_id", name="uq_billing_plan_price_external_price_id"),
    )
    op.create_index("ix_billing_plan_price_plan_id", "billing_plan_price", ["plan_id"])
    op.create_index(
        "ix_billing_plan_price_external_price_id",
        "billing_plan_price",
        ["external_price_id"],
    )

    # --- billing_subscription ---
    op.create_table(
        "billing_subscription",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "tenant_id",
            sa.Integer,
            sa.ForeignKey("tenant.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_price_id",
            sa.Integer,
            sa.ForeignKey("billing_plan_price.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("external_subscription_id", sa.String, nullable=True),
        sa.Column("status", sa.String, nullable=False, default="incomplete"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean, nullable=False, default=False),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint(
            "external_subscription_id",
            name="uq_billing_subscription_external_subscription_id",
        ),
        sa.CheckConstraint(
            f"status IN {_SUBSCRIPTION_STATUSES}",
            name="ck_billing_subscription_status",
        ),
    )
    op.create_index(
        "ix_billing_subscription_tenant_id", "billing_subscription", ["tenant_id"]
    )
    op.create_index(
        "ix_billing_subscription_external_subscription_id",
        "billing_subscription",
        ["external_subscription_id"],
    )
    # Partial unique index: at most one non-canceled subscription per tenant
    op.create_index(
        "uq_billing_subscription_active_tenant",
        "billing_subscription",
        ["tenant_id"],
        unique=True,
        postgresql_where=sa.text("status != 'canceled' AND deleted_at IS NULL"),
    )

    # --- billing_webhook_event ---
    op.create_table(
        "billing_webhook_event",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("external_event_id", sa.String, nullable=False, unique=True),
        sa.Column("event_type", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, default="received"),
        sa.Column("error", sa.String, nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index(
        "ix_billing_webhook_event_external_event_id",
        "billing_webhook_event",
        ["external_event_id"],
        unique=True,
    )

    # --- add is_protected to role ---
    op.add_column(
        "role",
        sa.Column("is_protected", sa.Boolean, nullable=False, server_default="0"),
    )

    now = datetime.now(UTC)

    # --- seed new permissions ---
    op.bulk_insert(
        permission_table,
        [
            {
                "name": p.value,
                "description": PERMISSION_DESCRIPTIONS[p],
                "created_at": now,
                "updated_at": now,
            }
            for p in _NEW_PERMISSIONS
        ],
    )

    # --- seed free plan (local-only, no Stripe IDs) ---
    # The free plan represents the default state for every new tenant.
    # _setup_new_tenant creates a billing_subscription row referencing this
    # price when a user registers; absence of a Stripe subscription is the
    # signal that the tenant is on the free tier.
    op.bulk_insert(
        plan_table,
        [
            {
                "name": "Free",
                "description": "Free plan",
                "external_product_id": None,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )
    conn = op.get_bind()
    plan_id = conn.execute(
        sa.text("SELECT id FROM billing_plan WHERE name = 'Free' LIMIT 1")
    ).scalar_one()
    op.bulk_insert(
        price_table,
        [
            {
                "plan_id": plan_id,
                "amount": 0,
                "currency": "dkk",
                "interval": "month",
                "interval_count": 1,
                "external_price_id": None,
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        permission_table.delete().where(
            permission_table.c.name.in_([p.value for p in _NEW_PERMISSIONS])
        )
    )

    op.drop_column("role", "is_protected")

    op.drop_index("uq_billing_subscription_active_tenant", table_name="billing_subscription")
    op.drop_table("billing_webhook_event")
    op.drop_table("billing_subscription")
    op.drop_table("billing_plan_price")
    op.drop_table("billing_plan")

    op.drop_index("ix_tenant_external_customer_id", table_name="tenant")
    op.drop_column("tenant", "trial_used")
    op.drop_column("tenant", "has_payment_method")
    op.drop_column("tenant", "external_customer_id")
