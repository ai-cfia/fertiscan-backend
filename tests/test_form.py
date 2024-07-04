import unittest
from pydantic import ValidationError
from backend import FertiliserForm

class TestFertiliserForm(unittest.TestCase):

    def test_valid_fertiliser_form(self):
        data = {
            "company_name": "ABC Company",
            "company_address": "123 Main St",
            "fertiliser_name": "Super Fertiliser",
            "npk": "10-5-5",
            "instructions_en": ["Use as directed"],
            "micronutrients_en": [{"nutrient": "Iron", "value": "2", "unit": "%"}],
            "specifications_en": [{"humidity": "Low", "ph": "7", "solubility": "High"}],
            "guaranteed_analysis": [{"nutrient": "Nitrogen", "value": "10", "unit": "%"}]
        }

        try:
            form = FertiliserForm(**data)
        except ValidationError as e:
            self.fail(f"Validation error: {e}")

        raw_form = form.model_dump()

        # Check if values match
        for key, expected_value in data.items():
            value = raw_form[key]
            self.assertEqual(expected_value, value, f"Value for key '{key}' does not match. Expected '{expected_value}', got '{value}'")

    def test_invalid_npk_format(self):
        invalid_data = {
            "company_name": "ABC Company",
            "fertiliser_name": "Super Fertiliser",
            "npk": "invalid-format",  # invalid npk format
            "instructions_en": ["Use as directed"],
            "micronutrients_en": [{"nutrient": "Iron", "value": "2", "unit": "%"}],
            "specifications_en": [{"humidity": "Low", "ph": "7", "solubility": "High"}],
            "guaranteed_analysis": [{"nutrient": "Nitrogen", "value": "10", "unit": "%"}]
        }

        with self.assertRaises(ValidationError):
            FertiliserForm(**invalid_data)

if __name__ == '__main__':
    unittest.main()
