from __future__ import annotations

from sqlalchemy import Boolean, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.enums import CategoryAttributeType
from app.db.mixins import PublicIdMixin, SoftDeleteMixin, TimestampMixin


class Category(PublicIdMixin, SoftDeleteMixin, TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        Index("ix_categories_parent_id", "parent_id"),
        Index("ix_categories_is_active_sort_order", "is_active", "sort_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="SET NULL"))
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    internal_name: Mapped[str] = mapped_column(String(150), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id",
        back_populates="children",
    )
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    translations: Mapped[list["CategoryTranslation"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    attributes: Mapped[list["CategoryAttribute"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
    )
    listings: Mapped[list["Listing"]] = relationship(back_populates="category")


class CategoryTranslation(TimestampMixin, Base):
    __tablename__ = "category_translations"
    __table_args__ = (
        UniqueConstraint("category_id", "locale", name="uq_category_translations_category_locale"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    locale: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped["Category"] = relationship(back_populates="translations")


class CategoryAttribute(TimestampMixin, Base):
    __tablename__ = "category_attributes"
    __table_args__ = (
        UniqueConstraint("category_id", "code", name="uq_category_attributes_category_code"),
        Index("ix_category_attributes_category_id_filterable", "category_id", "is_filterable"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    data_type: Mapped[CategoryAttributeType] = mapped_column(
        Enum(CategoryAttributeType, native_enum=False),
        nullable=False,
    )
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_filterable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    config_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    category: Mapped["Category"] = relationship(back_populates="attributes")
    options: Mapped[list["CategoryAttributeOption"]] = relationship(
        back_populates="attribute",
        cascade="all, delete-orphan",
    )


class CategoryAttributeOption(TimestampMixin, Base):
    __tablename__ = "category_attribute_options"
    __table_args__ = (
        UniqueConstraint(
            "category_attribute_id",
            "option_value",
            name="uq_category_attribute_options_attribute_value",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    category_attribute_id: Mapped[int] = mapped_column(
        ForeignKey("category_attributes.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_value: Mapped[str] = mapped_column(String(100), nullable=False)
    option_label: Mapped[str] = mapped_column(String(150), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    attribute: Mapped["CategoryAttribute"] = relationship(back_populates="options")
