"""Add listing view count column.

Revision ID: 20260329_0008
Revises: 20260327_0007
Create Date: 2026-03-29 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260329_0008"
down_revision = "20260327_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "listings",
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("listings", "view_count", server_default=None)


def downgrade() -> None:
    op.drop_column("listings", "view_count")
