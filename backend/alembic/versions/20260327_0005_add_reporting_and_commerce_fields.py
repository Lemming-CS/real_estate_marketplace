"""Add reporting and commerce workflow fields.

Revision ID: 20260327_0005
Revises: 20260327_0004
Create Date: 2026-03-27 18:45:00
"""

from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20260327_0005"
down_revision = "20260327_0004"
branch_labels = None
depends_on = None

OLD_PAYMENT_STATUS = sa.Enum("pending", "paid", "failed", "cancelled", "refunded", name="paymentstatus", native_enum=False)
NEW_PAYMENT_STATUS = sa.Enum(
    "pending",
    "successful",
    "failed",
    "cancelled",
    "refunded_ready",
    name="paymentstatus",
    native_enum=False,
)


def upgrade() -> None:
    connection = op.get_bind()

    op.add_column("reports", sa.Column("public_id", sa.String(length=36), nullable=True))
    op.add_column("payment_records", sa.Column("failure_reason", sa.Text(), nullable=True))
    op.add_column("payment_records", sa.Column("cancelled_at", sa.DateTime(), nullable=True))
    op.add_column("payment_records", sa.Column("refunded_ready_at", sa.DateTime(), nullable=True))
    op.add_column("promotion_packages", sa.Column("public_id", sa.String(length=36), nullable=True))
    op.add_column("promotions", sa.Column("target_city", sa.String(length=120), nullable=True))
    op.add_column("promotions", sa.Column("target_category_id", sa.Integer(), nullable=True))
    op.add_column("promotions", sa.Column("duration_days", sa.Integer(), nullable=True))
    op.add_column("promotions", sa.Column("price_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("promotions", sa.Column("currency_code", sa.String(length=3), nullable=True))

    report_rows = connection.execute(sa.text("SELECT id FROM reports")).fetchall()
    for row in report_rows:
        connection.execute(
            sa.text("UPDATE reports SET public_id = :public_id WHERE id = :id"),
            {"public_id": str(uuid4()), "id": row.id},
        )

    package_rows = connection.execute(sa.text("SELECT id FROM promotion_packages")).fetchall()
    for row in package_rows:
        connection.execute(
            sa.text("UPDATE promotion_packages SET public_id = :public_id WHERE id = :id"),
            {"public_id": str(uuid4()), "id": row.id},
        )

    promotion_rows = connection.execute(
        sa.text(
            """
            SELECT
                promotions.id AS promotion_id,
                promotion_packages.duration_days AS duration_days,
                promotion_packages.price_amount AS price_amount,
                promotion_packages.currency_code AS currency_code
            FROM promotions
            JOIN promotion_packages ON promotion_packages.id = promotions.promotion_package_id
            """
        )
    ).fetchall()
    for row in promotion_rows:
        connection.execute(
            sa.text(
                """
                UPDATE promotions
                SET duration_days = :duration_days,
                    price_amount = :price_amount,
                    currency_code = :currency_code
                WHERE id = :promotion_id
                """
            ),
            {
                "duration_days": row.duration_days,
                "price_amount": row.price_amount,
                "currency_code": row.currency_code,
                "promotion_id": row.promotion_id,
            },
        )

    with op.batch_alter_table("payment_records") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=OLD_PAYMENT_STATUS,
            type_=NEW_PAYMENT_STATUS,
            existing_nullable=False,
        )

    connection.execute(sa.text("UPDATE payment_records SET status = 'successful' WHERE status = 'paid'"))
    connection.execute(sa.text("UPDATE payment_records SET status = 'refunded_ready' WHERE status = 'refunded'"))

    with op.batch_alter_table("reports") as batch_op:
        batch_op.alter_column("public_id", existing_type=sa.String(length=36), nullable=False)
        batch_op.create_unique_constraint("uq_reports_public_id", ["public_id"])
        batch_op.create_index("ix_reports_reporter_user_id_created_at", ["reporter_user_id", "created_at"])
        batch_op.create_index("ix_reports_reported_user_id", ["reported_user_id"])

    with op.batch_alter_table("promotion_packages") as batch_op:
        batch_op.alter_column("public_id", existing_type=sa.String(length=36), nullable=False)
        batch_op.create_unique_constraint("uq_promotion_packages_public_id", ["public_id"])

    with op.batch_alter_table("promotions") as batch_op:
        batch_op.alter_column("duration_days", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("price_amount", existing_type=sa.Numeric(12, 2), nullable=False)
        batch_op.alter_column("currency_code", existing_type=sa.String(length=3), nullable=False)
        batch_op.create_foreign_key(
            "fk_promotions_target_category_id_categories",
            "categories",
            ["target_category_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_promotions_target_city_status", ["target_city", "status"])
        batch_op.create_index("ix_promotions_target_category_status", ["target_category_id", "status"])


def downgrade() -> None:
    with op.batch_alter_table("promotions") as batch_op:
        batch_op.drop_index("ix_promotions_target_category_status")
        batch_op.drop_index("ix_promotions_target_city_status")
        batch_op.drop_constraint("fk_promotions_target_category_id_categories", type_="foreignkey")
        batch_op.drop_column("currency_code")
        batch_op.drop_column("price_amount")
        batch_op.drop_column("duration_days")
        batch_op.drop_column("target_category_id")
        batch_op.drop_column("target_city")

    with op.batch_alter_table("promotion_packages") as batch_op:
        batch_op.drop_constraint("uq_promotion_packages_public_id", type_="unique")
        batch_op.drop_column("public_id")

    connection = op.get_bind()

    with op.batch_alter_table("payment_records") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=NEW_PAYMENT_STATUS,
            type_=OLD_PAYMENT_STATUS,
            existing_nullable=False,
        )
        batch_op.drop_column("refunded_ready_at")
        batch_op.drop_column("cancelled_at")
        batch_op.drop_column("failure_reason")
    
    connection.execute(sa.text("UPDATE payment_records SET status = 'paid' WHERE status = 'successful'"))
    connection.execute(sa.text("UPDATE payment_records SET status = 'refunded' WHERE status = 'refunded_ready'"))


    with op.batch_alter_table("reports") as batch_op:
        batch_op.drop_index("ix_reports_reported_user_id")
        batch_op.drop_index("ix_reports_reporter_user_id_created_at")
        batch_op.drop_constraint("uq_reports_public_id", type_="unique")
        batch_op.drop_column("public_id")
