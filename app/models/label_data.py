from enum import Enum
from typing import Annotated

import phonenumbers
from pydantic import BaseModel, Field
from pydantic_extra_types.phone_numbers import PhoneNumberValidator

CAPhoneNumber = Annotated[
    str | phonenumbers.PhoneNumber,
    PhoneNumberValidator(
        supported_regions=["US", "CA"],
        number_format="E164",
        default_region="CA",
    ),
]


class Organization(BaseModel):
    name: str | None = None
    address: str | None = None
    website: str | None = None
    phone_number: CAPhoneNumber | None = None


class RegistrationType(str, Enum):
    fertilizer = "fertilizer_product"
    ingredient = "ingredient_component"


class RegistrationNumber(BaseModel):
    identifier: str | None = Field(None, pattern=r"^\d{7}[A-Za-z]$")
    type: RegistrationType | None = None


class Quantity(BaseModel):
    value: float | None = None
    unit: str | None = None


class Nutrient(Quantity):
    nutrient: str | None = None


class GuaranteedAnalysis(BaseModel):
    title: str | None = None
    nutrients: list[Nutrient] = []
    is_minimal: bool | None = None


class LabelData(BaseModel):
    organizations: list[Organization] = []
    fertiliser_name: str | None = None
    registration_number: list[RegistrationNumber] = []
    lot_number: str | None = None
    weight: list[Quantity] = []
    density: Quantity | None = None
    volume: Quantity | None = None
    npk: str | None = Field(None, pattern=r"^\d+(\.\d+)?-\d+(\.\d+)?-\d+(\.\d+)?$")
    guaranteed_analysis_en: GuaranteedAnalysis | None = None
    guaranteed_analysis_fr: GuaranteedAnalysis | None = None
    cautions_en: list[str] | None = None
    cautions_fr: list[str] | None = None
    instructions_en: list[str] = []
    instructions_fr: list[str] = []
    ingredients_en: list[Nutrient] = []
    ingredients_fr: list[Nutrient] = []
