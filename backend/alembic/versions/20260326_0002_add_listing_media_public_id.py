"""Add public_id to listing_media.

Revision ID: 20260326_0002
Revises: 20260326_0001
Create Date: 2026-03-26 11:00:00
"""

from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20260326_0002"
down_revision = "20260326_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listing_media",
        sa.Column("public_id", sa.String(length=36), nullable=True),
    )

    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM listing_media")).fetchall()
    for row in rows:
        connection.execute(
            sa.text("UPDATE listing_media SET public_id = :public_id WHERE id = :id"),
            {"public_id": str(uuid4()), "id": row.id},
        )

    op.alter_column(
        "listing_media",
        "public_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_listing_media_public_id",
        "listing_media",
        ["public_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_listing_media_public_id", "listing_media", type_="unique")
    op.drop_column("listing_media", "public_id")