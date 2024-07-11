import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class npkError(ValueError):
    pass

class NutrientValue(BaseModel):
    nutrient: str
    value: Optional[str]
    unit: Optional[str]

    @field_validator('value', mode='before', check_fields=True)
    def convert_value(cls, v):
        if isinstance(v, (int, float)):
            return str(v)
        return v

class Specification(BaseModel):
    humidity: Optional[str] = Field(..., alias='humidity')
    ph: Optional[str] = Field(..., alias='ph')
    solubility: Optional[str]

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
    npk: Optional[str] = Field(None)
    guaranteed_analysis: List[NutrientValue] = []
    warranty: Optional[str] = ""
    cautions_en: List[str] = None
    instructions_en: List[str] = []
    micronutrients_en: List[NutrientValue] = []
    organic_ingredients_en: List[NutrientValue] = []
    inert_ingredients_en: List[str] = []
    specifications_en: List[Specification] = []
    first_aid_en: List[str] = None
    cautions_fr: List[str] = None
    instructions_fr: List[str] = []
    micronutrients_fr: List[NutrientValue] = []
    organic_ingredients_fr: List[NutrientValue] = []
    inert_ingredients_fr: List[str] = []
    specifications_fr: List[Specification] = []
    first_aid_fr: List[str] = None

    @field_validator('weight_kg', 'weight_lb', 'density', 'volume', mode='before', check_fields=True)
    def convert_values(cls, v):
        if isinstance(v, (int, float)):
            return str(v)
        return v
    
    @field_validator('npk', mode='before')
    def validate_npk(cls, v):
        if v is not None:
            pattern = re.compile(r'^(\d+(\.\d+)?-\d+(\.\d+)?-\d+(\.\d+)?)?$')
            if not pattern.match(v):
                raise npkError('npk must be in the format "number-number-number"')
        return v

    class Config:
        populate_by_name = True
