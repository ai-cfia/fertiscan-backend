import unittest
from pydantic import ValidationError
from backend import FertiliserForm

class TestFertiliserForm(unittest.TestCase):

    def test_valid_json(self):
        valid_data = {
            "company_name": "Company Inc.",
            "company_address": "123 Street",
            "company_website": "http://company.com",
            "company_phone_number": "+1234567890",
            "manufacturer_name": "Manufacturer Inc.",
            "manufacturer_address": "456 Avenue",
            "manufacturer_website": "http://manufacturer.com",
            "manufacturer_phone_number": "+0987654321",
            "fertiliser_name": "Super Fertilizer",
            "registration_number": "ABC12345",
            "lot_number": "LOT67890",
            "weight_kg": "50kg",
            "weight_lb": "110lb",
            "density": "1.2",
            "volume": "20L",
            "warranty": "1 year",
            "npk": "10-10-10",
            "instructions_en": ["Apply evenly.", "Water after application."],
            "micronutrients_en": [{"name": "Zinc", "percentage": "0.05"}],
            "organic_ingredients_en": [{"name": "Compost", "percentage": "40"}],
            "inert_ingredients_en": ["Sand"],
            "specifications_en": [{"humidity": "5", "ph": "6.5", "solubility": "high"}],
            "cautions_en": [
                "Wear gloves.",
                "Keep out of reach of children.",
            ],
            "first_aid_en": ["Rinse eyes with water."],
            "cautions_fr": [
                "Portez des gants.",
                "Garder hors de portée des enfants.",
            ],
            "instructions_fr": ["Appliquer uniformément.", "Arroser après application."],
            "micronutrients_fr": [{"name": "Zinc", "percentage": "0.05"}],
            "organic_ingredients_fr": [{"name": "Compost", "percentage": "40"}],
            "inert_ingredients_fr": ["Sable"],
            "specifications_fr": [{"humidity": "5", "ph": "6.5", "solubility": "haute"}],
            "first_aid_fr": ["Rincer les yeux avec de l'eau."],
            "guaranteed_analysis": [{"nutrient": "Nitrogen", "percentage": "10"}]
        }

        form = FertiliserForm(**valid_data)
        self.assertIsInstance(form, FertiliserForm)

    def test_invalid_npk(self):
        invalid_data = {
            "npk": "10-10",
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

    def test_invalid_percentage(self):
        invalid_data = {
            "micronutrients_en": [{"name": "Zinc", "percentage": "five"}],
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

    def test_invalid_weight_kg(self):
        invalid_data = {
            "weight_kg": "50pounds",
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

    def test_invalid_weight_lb(self):
        invalid_data = {
            "weight_lb": "110kg",
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

    def test_invalid_density(self):
        invalid_data = {
            "density": "density",
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

    def test_invalid_humidity(self):
        invalid_data = {
            "specifications_en": [{"humidity": "high", "ph": "6.5", "solubility": "high"}],
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

    def test_invalid_ph(self):
        invalid_data = {
            "specifications_en": [{"humidity": "5", "ph": "acidic", "solubility": "high"}],
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

    def test_invalid_solubility(self):
        invalid_data = {
            "specifications_en": [{"humidity": "5", "ph": "6.5", "solubility": "very"}],
        }
        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

if __name__ == "__main__":
    unittest.main()
