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

        self.assertEqual(form.company_name, "ABC Company")
        self.assertEqual(form.fertiliser_name, "Super Fertiliser")
        self.assertEqual(form.npk, "10-5-5")
        self.assertEqual(form.instructions_en, ["Use as directed"])
        self.assertEqual(len(form.micronutrients_en), 1)
        self.assertEqual(form.micronutrients_en[0].nutrient, "Iron")
        self.assertEqual(form.micronutrients_en[0].value, "2")
        self.assertEqual(form.micronutrients_en[0].unit, "%")
        self.assertEqual(len(form.specifications_en), 1)
        self.assertEqual(form.specifications_en[0].humidity, "Low")
        self.assertEqual(form.specifications_en[0].ph, "7")
        self.assertEqual(form.specifications_en[0].solubility, "High")
        self.assertEqual(len(form.guaranteed_analysis), 1)
        self.assertEqual(form.guaranteed_analysis[0].nutrient, "Nitrogen")
        self.assertEqual(form.guaranteed_analysis[0].value, "10")
        self.assertEqual(form.guaranteed_analysis[0].unit, "%")

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
