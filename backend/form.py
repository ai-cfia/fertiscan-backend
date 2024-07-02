from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class NutrientValue(BaseModel):
    nutrient: str
    value: str
    unit: str

    @field_validator('value', mode='before', check_fields=True)
    def convert_value(cls, v):
        if isinstance(v, (int, float)):
            return str(v)
        return v

class Specification(BaseModel):
    humidity: Optional[str] = Field(..., alias='humidity')
    ph: Optional[str] = Field(..., alias='ph')
    solubility: str

    @field_validator('humidity', 'ph', 'solubility', mode='before', check_fields=True)
    def convert_specification_values(cls, v):
        if isinstance(v, (int, float)):
            return str(v)
        return v

class FertiliserForm(BaseModel):
    company_name: Optional[str] = ""
    company_address: Optional[str] = ""
    company_website: Optional[str] = ""
    company_phone_number: Optional[str] = ""
    manufacturer_name: Optional[str] = ""
    manufacturer_address: Optional[str] = ""
    manufacturer_website: Optional[str] = ""
    manufacturer_phone_number: Optional[str] = ""
    fertiliser_name: Optional[str] = ""
    registration_number: Optional[str] = ""
    lot_number: Optional[str] = ""
    weight_kg: Optional[str] = None
    weight_lb: Optional[str] = None
    density: Optional[str] = None
    volume: Optional[str] = None
    warranty: Optional[str] = ""
    npk: str = Field(..., pattern=r'^(\d+-\d+-\d+)?$')
    instructions_en: List[str] = []
    micronutrients_en: List[NutrientValue] = []
    organic_ingredients_en: List[NutrientValue] = []
    inert_ingredients_en: List[str] = []
    specifications_en: List[Specification] = []
    cautions_en: List[str] = None
    first_aid_en: List[str] = None
    instructions_fr: List[str] = []
    micronutrients_fr: List[NutrientValue] = []
    organic_ingredients_fr: List[NutrientValue] = []
    inert_ingredients_fr: List[str] = []
    specifications_fr: List[Specification] = []
    cautions_fr: List[str] = None
    first_aid_fr: List[str] = None
    guaranteed_analysis: List[NutrientValue] = []

    @field_validator('weight_kg', 'weight_lb', 'density', 'volume', mode='before', check_fields=True)
    def convert_values(cls, v):
        if isinstance(v, (int, float)):
            return str(v)
        return v

    class Config:
        populate_by_name = True
