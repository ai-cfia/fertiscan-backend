from typing import List, Optional
from pydantic import BaseModel, Field

class NutrientAnalysis(BaseModel):
    nutrient: str
    percentage: str

class Micronutrient(BaseModel):
    name: str
    percentage: str

class OrganicIngredient(BaseModel):
    name: str
    percentage: str

class Specification(BaseModel):
    humidity: Optional[str] = Field(..., alias='humidity')
    ph: Optional[str] = Field(..., alias='ph')
    solubility: str

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
    fertiliser_registration_number: Optional[str] = ""
    fertiliser_lot_number: Optional[str] = ""
    fertiliser_weight_kg: Optional[str] = None
    fertiliser_weight_lb: Optional[str] = None
    fertiliser_density: Optional[str] = None
    fertiliser_volume: Optional[str] = None
    warranty: Optional[str] = ""
    fertiliser_npk: str = Field(..., pattern=r'^(\d+-\d+-\d+)?$')
    precautions_en: Optional[str] = None
    instructions_en: List[str] = []
    micronutrients_en: List[Micronutrient] = []
    organic_ingredients_en: List[OrganicIngredient] = []
    inert_ingredients_en: List[str] = []
    specifications_en: List[Specification] = []
    cautions_en: Optional[str] = None
    first_aid_en: Optional[str] = None
    precautions_fr: Optional[str] = None
    instructions_fr: List[str] = []
    micronutrients_fr: List[Micronutrient] = []
    organic_ingredients_fr: List[OrganicIngredient] = []
    inert_ingredients_fr: List[str] = []
    specifications_fr: List[Specification] = []
    cautions_fr: Optional[str] = None
    first_aid_fr: Optional[str] = None
    fertiliser_guaranteed_analysis: List[NutrientAnalysis] = []

    class Config:
        populate_by_name = True
