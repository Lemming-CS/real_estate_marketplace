"""Add messaging indexes and attachment public_id.

Revision ID: 20260327_0004
Revises: 20260327_0003
Create Date: 2026-03-27 12:00:00
"""

from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20260327_0004"
down_revision = "20260327_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.add_column("message_attachments", sa.Column("public_id", sa.String(length=36), nullable=True))
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM message_attachments")).fetchall()
    for row in rows:
        connection.execute(
            sa.text("UPDATE message_attachments SET public_id = :public_id WHERE id = :id"),
            {"public_id": str(uuid4()), "id": row.id},
        )
    op.alter_column(
        "message_attachments",
        "public_id",
        existing_type=sa.String(length=36),
        nullable=False,
    )
    op.create_unique_constraint("uq_message_attachments_public_id", "message_attachments", ["public_id"])
    op.create_index("ix_message_attachments_message_id", "message_attachments", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_message_attachments_message_id", table_name="message_attachments")
    op.drop_constraint("uq_message_attachments_public_id", "message_attachments", type_="unique")
    op.drop_column("message_attachments", "public_id")
