"""Normalize real estate enum values.

Revision ID: 20260327_0007
Revises: 20260327_0006
Create Date: 2026-03-27 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260327_0007"
down_revision = "20260327_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE listings SET purpose = 'rent' WHERE purpose = 'RENT'"))
    connection.execute(sa.text("UPDATE listings SET purpose = 'sale' WHERE purpose = 'SALE'"))
    connection.execute(sa.text("UPDATE listings SET property_type = 'apartment' WHERE property_type = 'APARTMENT'"))
    connection.execute(sa.text("UPDATE listings SET property_type = 'house' WHERE property_type = 'HOUSE'"))


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE listings SET purpose = 'RENT' WHERE purpose = 'rent'"))
    connection.execute(sa.text("UPDATE listings SET purpose = 'SALE' WHERE purpose = 'sale'"))
    connection.execute(sa.text("UPDATE listings SET property_type = 'APARTMENT' WHERE property_type = 'apartment'"))
    connection.execute(sa.text("UPDATE listings SET property_type = 'HOUSE' WHERE property_type = 'house'"))