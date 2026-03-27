"""Align listing schema to the real-estate marketplace domain.

Revision ID: 20260327_0006
Revises: 20260327_0005
Create Date: 2026-03-27 19:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260327_0006"
down_revision = "20260327_0005"
branch_labels = None
depends_on = None


LISTING_PURPOSE = sa.Enum("rent", "sale", name="listingpurpose", native_enum=False)
PROPERTY_TYPE = sa.Enum("apartment", "house", name="propertytype", native_enum=False)
LISTING_CONDITION = sa.Enum(
    "new",
    "like_new",
    "used_good",
    "used_fair",
    "for_parts",
    name="listingcondition",
    native_enum=False,
)


def upgrade() -> None:
    op.add_column("listings", sa.Column("purpose", LISTING_PURPOSE, nullable=True))
    op.add_column("listings", sa.Column("property_type", PROPERTY_TYPE, nullable=True))
    op.add_column("listings", sa.Column("district", sa.String(length=120), nullable=True))
    op.add_column("listings", sa.Column("address_text", sa.String(length=255), nullable=True))
    op.add_column("listings", sa.Column("map_label", sa.String(length=120), nullable=True))
    op.add_column("listings", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("listings", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("listings", sa.Column("room_count", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("area_sqm", sa.Numeric(10, 2), nullable=True))
    op.add_column("listings", sa.Column("floor", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("total_floors", sa.Integer(), nullable=True))
    op.add_column("listings", sa.Column("furnished", sa.Boolean(), nullable=True))

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            """
            SELECT listings.id, listings.city, categories.slug
            FROM listings
            JOIN categories ON categories.id = listings.category_id
            """
        )
    ).fetchall()

    for row in rows:
        property_type = "house" if "house" in (row.slug or "").lower() else "apartment"
        total_floors = 2 if property_type == "house" else 9
        floor = 1 if property_type == "apartment" else 2
        connection.execute(
            sa.text(
                """
                UPDATE listings
                SET purpose = :purpose,
                    property_type = :property_type,
                    address_text = :address_text,
                    map_label = :map_label,
                    latitude = :latitude,
                    longitude = :longitude,
                    room_count = :room_count,
                    area_sqm = :area_sqm,
                    floor = :floor,
                    total_floors = :total_floors
                WHERE id = :id
                """
            ),
            {
                "id": row.id,
                "purpose": "sale",
                "property_type": property_type,
                "address_text": f"{row.city or 'Bishkek'} legacy address",
                "map_label": row.city or "Legacy area",
                "latitude": "42.8746210",
                "longitude": "74.5697620",
                "room_count": 1,
                "area_sqm": "45.00",
                "floor": floor,
                "total_floors": total_floors,
            },
        )

    with op.batch_alter_table("listings") as batch_op:
        batch_op.alter_column("purpose", existing_type=LISTING_PURPOSE, nullable=False)
        batch_op.alter_column("property_type", existing_type=PROPERTY_TYPE, nullable=False)
        batch_op.alter_column("address_text", existing_type=sa.String(length=255), nullable=False)
        batch_op.alter_column("latitude", existing_type=sa.Numeric(10, 7), nullable=False)
        batch_op.alter_column("longitude", existing_type=sa.Numeric(10, 7), nullable=False)
        batch_op.alter_column("room_count", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("area_sqm", existing_type=sa.Numeric(10, 2), nullable=False)
        batch_op.alter_column("item_condition", existing_type=LISTING_CONDITION, nullable=True)

    op.create_index(
        "ix_listings_purpose_property_status_published_at",
        "listings",
        ["purpose", "property_type", "status", "published_at"],
    )
    op.create_index(
        "ix_listings_city_purpose_property_price",
        "listings",
        ["city", "purpose", "property_type", "price_amount"],
    )
    op.create_index("ix_listings_status_area_sqm", "listings", ["status", "area_sqm"])
    op.create_index("ix_listings_status_room_count", "listings", ["status", "room_count"])


def downgrade() -> None:
    op.drop_index("ix_listings_status_room_count", table_name="listings")
    op.drop_index("ix_listings_status_area_sqm", table_name="listings")
    op.drop_index("ix_listings_city_purpose_property_price", table_name="listings")
    op.drop_index("ix_listings_purpose_property_status_published_at", table_name="listings")

    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            UPDATE listings
            SET item_condition = COALESCE(item_condition, 'used_good')
            """
        )
    )

    with op.batch_alter_table("listings") as batch_op:
        batch_op.alter_column("item_condition", existing_type=LISTING_CONDITION, nullable=False)
        batch_op.drop_column("furnished")
        batch_op.drop_column("total_floors")
        batch_op.drop_column("floor")
        batch_op.drop_column("area_sqm")
        batch_op.drop_column("room_count")
        batch_op.drop_column("longitude")
        batch_op.drop_column("latitude")
        batch_op.drop_column("map_label")
        batch_op.drop_column("address_text")
        batch_op.drop_column("district")
        batch_op.drop_column("property_type")
        batch_op.drop_column("purpose")
