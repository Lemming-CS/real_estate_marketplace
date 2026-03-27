from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.db.enums import CategoryAttributeType

LocaleCode = Literal["en", "ru"]


class CategoryAttributeOptionInput(BaseModel):
    option_value: str = Field(min_length=1, max_length=100)
    option_label: str = Field(min_length=1, max_length=150)
    sort_order: int = Field(default=0, ge=0)


class CategoryAttributeInput(BaseModel):
    code: str = Field(min_length=2, max_length=100)
    display_name: str = Field(min_length=2, max_length=150)
    data_type: CategoryAttributeType
    unit: str | None = Field(default=None, max_length=32)
    is_required: bool = False
    is_filterable: bool = False
    sort_order: int = Field(default=0, ge=0)
    config_json: dict[str, Any] | list[Any] | None = None
    options: list[CategoryAttributeOptionInput] = Field(default_factory=list)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().lower().replace("-", "_")

    @model_validator(mode="after")
    def validate_options(self) -> "CategoryAttributeInput":
        if self.data_type == CategoryAttributeType.SELECT and not self.options:
            raise ValueError("Select attributes must include at least one option.")
        if self.data_type != CategoryAttributeType.SELECT and self.options:
            raise ValueError("Only select attributes can define options.")
        return self


class CategoryTranslationInput(BaseModel):
    locale: LocaleCode
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=1000)


class CategoryCreateRequest(BaseModel):
    parent_public_id: str | None = None
    slug: str = Field(min_length=2, max_length=100)
    internal_name: str = Field(min_length=2, max_length=150)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)
    translations: list[CategoryTranslationInput] = Field(default_factory=list)
    attributes: list[CategoryAttributeInput] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def validate_nested_uniques(self) -> "CategoryCreateRequest":
        _validate_unique_locales(self.translations)
        _validate_unique_attribute_codes(self.attributes)
        return self


class CategoryUpdateRequest(BaseModel):
    parent_public_id: str | None = None
    slug: str | None = Field(default=None, min_length=2, max_length=100)
    internal_name: str | None = Field(default=None, min_length=2, max_length=150)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    translations: list[CategoryTranslationInput] | None = None
    attributes: list[CategoryAttributeInput] | None = None

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else value

    @model_validator(mode="after")
    def validate_nested_uniques(self) -> "CategoryUpdateRequest":
        if self.translations is not None:
            _validate_unique_locales(self.translations)
        if self.attributes is not None:
            _validate_unique_attribute_codes(self.attributes)
        return self


class CategoryAttributeOptionSchema(BaseModel):
    option_value: str
    option_label: str
    sort_order: int


class CategoryAttributeSchema(BaseModel):
    code: str
    display_name: str
    data_type: CategoryAttributeType
    unit: str | None = None
    is_required: bool
    is_filterable: bool
    sort_order: int
    config_json: dict[str, Any] | list[Any] | None = None
    options: list[CategoryAttributeOptionSchema]


class CategoryTranslationSchema(BaseModel):
    locale: str
    name: str
    description: str | None = None


class AdminCategorySchema(BaseModel):
    public_id: str
    parent_public_id: str | None = None
    slug: str
    internal_name: str
    is_active: bool
    sort_order: int
    deleted_at: str | None = None
    translations: list[CategoryTranslationSchema]
    attributes: list[CategoryAttributeSchema]


class PublicCategorySchema(BaseModel):
    public_id: str
    parent_public_id: str | None = None
    slug: str
    name: str
    description: str | None = None
    locale: str
    sort_order: int
    attributes: list[CategoryAttributeSchema]
    children: list["PublicCategorySchema"] = Field(default_factory=list)


def _validate_unique_locales(translations: list[CategoryTranslationInput]) -> None:
    locales = [translation.locale for translation in translations]
    if len(locales) != len(set(locales)):
        raise ValueError("Category translations must use unique locales.")


def _validate_unique_attribute_codes(attributes: list[CategoryAttributeInput]) -> None:
    codes = [attribute.code for attribute in attributes]
    if len(codes) != len(set(codes)):
        raise ValueError("Category attributes must use unique codes.")


PublicCategorySchema.model_rebuild()
