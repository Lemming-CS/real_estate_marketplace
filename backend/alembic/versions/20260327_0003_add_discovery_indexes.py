"""Add discovery indexes for listings and favorites.

Revision ID: 20260327_0003
Revises: 20260326_0002
Create Date: 2026-03-27 10:00:00
"""

from __future__ import annotations

from alembic import op


revision = "20260327_0003"
down_revision = "20260326_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_listings_status_city_published_at",
        "listings",
        ["status", "city", "published_at"],
    )
    op.create_index(
        "ix_listings_status_price_amount",
        "listings",
        ["status", "price_amount"],
    )
    op.create_index("ix_listings_title", "listings", ["title"])
    op.create_index(
        "ix_favorites_user_id_created_at",
        "favorites",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_favorites_user_id_created_at", table_name="favorites")
    op.drop_index("ix_listings_title", table_name="listings")
    op.drop_index("ix_listings_status_price_amount", table_name="listings")
    op.drop_index("ix_listings_status_city_published_at", table_name="listings")
