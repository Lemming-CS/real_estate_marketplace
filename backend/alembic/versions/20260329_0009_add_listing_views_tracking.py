"""Add deduplicated listing view tracking.

Revision ID: 20260329_0009
Revises: 20260329_0008
Create Date: 2026-03-29 00:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260329_0009"
down_revision = "20260329_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "listing_views",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("guest_token", sa.String(length=64), nullable=True),
        sa.Column("last_viewed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("listing_id", "guest_token", name="uq_listing_views_listing_guest"),
        sa.UniqueConstraint("listing_id", "user_id", name="uq_listing_views_listing_user"),
    )
    op.create_index(
        "ix_listing_views_listing_id_last_viewed_at",
        "listing_views",
        ["listing_id", "last_viewed_at"],
        unique=False,
    )
    op.create_index("ix_listing_views_user_id", "listing_views", ["user_id"], unique=False)
    op.create_index("ix_listing_views_guest_token", "listing_views", ["guest_token"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_listing_views_guest_token", table_name="listing_views")
    op.drop_index("ix_listing_views_user_id", table_name="listing_views")
    op.drop_index("ix_listing_views_listing_id_last_viewed_at", table_name="listing_views")
    op.drop_table("listing_views")
