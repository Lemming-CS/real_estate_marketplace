"""Add normalized KGS price for listing sorting and filtering.

Revision ID: 20260329_0010
Revises: 20260329_0009
Create Date: 2026-03-29 01:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260329_0010"
down_revision = "20260329_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column(
            "normalized_price_kgs",
            sa.Numeric(14, 2),
            nullable=False,
            server_default="0.00",
        ),
    )
    op.execute(
        """
        UPDATE listings
        SET normalized_price_kgs = CASE UPPER(currency_code)
            WHEN 'USD' THEN ROUND(price_amount * 87.5, 2)
            WHEN 'KGS' THEN ROUND(price_amount, 2)
            ELSE ROUND(price_amount, 2)
        END
        """
    )
    op.alter_column("listings", "normalized_price_kgs", server_default=None)
    op.create_index(
        "ix_listings_status_normalized_price_kgs",
        "listings",
        ["status", "normalized_price_kgs"],
        unique=False,
    )
    op.create_index(
        "ix_listings_city_purpose_property_normalized_price_kgs",
        "listings",
        ["city", "purpose", "property_type", "normalized_price_kgs"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_listings_city_purpose_property_normalized_price_kgs", table_name="listings")
    op.drop_index("ix_listings_status_normalized_price_kgs", table_name="listings")
    op.drop_column("listings", "normalized_price_kgs")
