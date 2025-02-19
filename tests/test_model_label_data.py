from unittest import TestCase

import phonenumbers
from pydantic import ValidationError

from app.models.label_data import (
    GuaranteedAnalysis,
    LabelData,
    Nutrient,
    Organization,
    Quantity,
    RegistrationNumber,
    RegistrationType,
)


class TestOrganizationModel(TestCase):
    def test_valid_phone_number(self):
        data = {
            "name": "Test Org",
            "address": "123 Test Street",
            "website": "https://test.org",
            "phone_number": "+14165551234",
        }
        org = Organization.model_validate(data)
        self.assertEqual(org.phone_number, "+14165551234")

    def test_valid_parsed_phone_number(self):
        phone_obj = phonenumbers.parse("+14165551234", "US")
        data = {"phone_number": phone_obj}
        org = Organization.model_validate(data)
        self.assertEqual(org.phone_number, "+14165551234")

    def test_invalid_phone_number(self):
        data = {"phone_number": "invalid_number"}
        with self.assertRaises(ValidationError):
            Organization.model_validate(data)

    def test_invalid_phone_region(self):
        data = {"phone_number": "+4915123456789"}
        with self.assertRaises(ValidationError):
            Organization.model_validate(data)

    def test_optional_phone_number(self):
        data = {"name": "No Phone Org"}
        org = Organization.model_validate(data)
        self.assertIsNone(org.phone_number)

    def test_optional_fields(self):
        data = {}
        org = Organization.model_validate(data)
        self.assertIsNone(org.name)
        self.assertIsNone(org.address)
        self.assertIsNone(org.website)
        self.assertIsNone(org.phone_number)


class TestRegistrationNumber(TestCase):
    def test_valid_registration_number(self):
        data = {"identifier": "1234567A", "type": "fertilizer_product"}
        reg_num = RegistrationNumber.model_validate(data)
        self.assertEqual(reg_num.identifier, "1234567A")
        self.assertEqual(reg_num.type, RegistrationType.fertilizer)

    def test_valid_registration_number_lowercase(self):
        data = {"identifier": "7654321z", "type": "ingredient_component"}
        reg_num = RegistrationNumber.model_validate(data)
        self.assertEqual(reg_num.identifier, "7654321z")
        self.assertEqual(reg_num.type, RegistrationType.ingredient)

    def test_valid_none_identifier(self):
        data = {"identifier": None, "type": "ingredient_component"}
        reg_num = RegistrationNumber.model_validate(data)
        self.assertIsNone(reg_num.identifier)
        self.assertEqual(reg_num.type, RegistrationType.ingredient)

    def test_invalid_empty_identifier(self):
        data = {"identifier": "", "type": "fertilizer_product"}
        with self.assertRaises(ValidationError):
            RegistrationNumber.model_validate(data)

    def test_invalid_identifier_too_short(self):
        data = {"identifier": "123456", "type": "fertilizer_product"}
        with self.assertRaises(ValidationError):
            RegistrationNumber.model_validate(data)

    def test_invalid_identifier_too_long(self):
        data = {"identifier": "12345678A", "type": "fertilizer_product"}
        with self.assertRaises(ValidationError):
            RegistrationNumber.model_validate(data)

    def test_invalid_identifier_special_char(self):
        data = {"identifier": "1234567!", "type": "fertilizer_product"}
        with self.assertRaises(ValidationError):
            RegistrationNumber.model_validate(data)

    def test_invalid_identifier_missing_letter(self):
        data = {"identifier": "1234567", "type": "fertilizer_product"}
        with self.assertRaises(ValidationError):
            RegistrationNumber.model_validate(data)

    def test_invalid_identifier_extra_digits(self):
        data = {"identifier": "12345678B", "type": "fertilizer_product"}
        with self.assertRaises(ValidationError):
            RegistrationNumber.model_validate(data)

    def test_invalid_registration_type(self):
        data = {"identifier": "1234567A", "type": "invalid_type"}
        with self.assertRaises(ValidationError):
            RegistrationNumber.model_validate(data)


class TestQuantity(TestCase):
    def test_valid_quantity(self):
        data = {"value": 10.5, "unit": "kg"}
        qty = Quantity.model_validate(data)
        self.assertEqual(qty.value, 10.5)
        self.assertEqual(qty.unit, "kg")

    def test_valid_none_value(self):
        data = {"value": None, "unit": "g"}
        qty = Quantity.model_validate(data)
        self.assertIsNone(qty.value)
        self.assertEqual(qty.unit, "g")

    def test_valid_none_unit(self):
        data = {"value": 5.0, "unit": None}
        qty = Quantity.model_validate(data)
        self.assertEqual(qty.value, 5.0)
        self.assertIsNone(qty.unit)

    def test_valid_none_value_and_unit(self):
        data = {"value": None, "unit": None}
        qty = Quantity.model_validate(data)
        self.assertIsNone(qty.value)
        self.assertIsNone(qty.unit)

    def test_invalid_value_type(self):
        data = {"value": "invalid", "unit": "kg"}
        with self.assertRaises(ValidationError):
            Quantity.model_validate(data)

    def test_invalid_unit_type(self):
        data = {"value": 10.5, "unit": 123}
        with self.assertRaises(ValidationError):
            Quantity.model_validate(data)


class TestNutrient(TestCase):
    def test_valid_nutrient(self):
        data = {"value": 12.5, "unit": "mg", "nutrient": "Calcium"}
        nutrient = Nutrient.model_validate(data)
        self.assertEqual(nutrient.value, 12.5)
        self.assertEqual(nutrient.unit, "mg")
        self.assertEqual(nutrient.nutrient, "Calcium")

    def test_valid_none_value(self):
        data = {"value": None, "unit": "g", "nutrient": "Iron"}
        nutrient = Nutrient.model_validate(data)
        self.assertIsNone(nutrient.value)
        self.assertEqual(nutrient.unit, "g")
        self.assertEqual(nutrient.nutrient, "Iron")

    def test_valid_none_unit(self):
        data = {"value": 5.0, "unit": None, "nutrient": "Vitamin C"}
        nutrient = Nutrient.model_validate(data)
        self.assertEqual(nutrient.value, 5.0)
        self.assertIsNone(nutrient.unit)
        self.assertEqual(nutrient.nutrient, "Vitamin C")

    def test_valid_none_nutrient(self):
        data = {"value": 3.2, "unit": "g", "nutrient": None}
        nutrient = Nutrient.model_validate(data)
        self.assertEqual(nutrient.value, 3.2)
        self.assertEqual(nutrient.unit, "g")
        self.assertIsNone(nutrient.nutrient)

    def test_valid_none_all_fields(self):
        data = {"value": None, "unit": None, "nutrient": None}
        nutrient = Nutrient.model_validate(data)
        self.assertIsNone(nutrient.value)
        self.assertIsNone(nutrient.unit)
        self.assertIsNone(nutrient.nutrient)

    def test_invalid_value_type(self):
        data = {"value": "invalid", "unit": "mg", "nutrient": "Calcium"}
        with self.assertRaises(ValidationError):
            Nutrient.model_validate(data)

    def test_invalid_unit_type(self):
        data = {"value": 10.5, "unit": 123, "nutrient": "Potassium"}
        with self.assertRaises(ValidationError):
            Nutrient.model_validate(data)

    def test_invalid_nutrient_type(self):
        data = {"value": 8.0, "unit": "g", "nutrient": 456}
        with self.assertRaises(ValidationError):
            Nutrient.model_validate(data)


class TestGuaranteedAnalysis(TestCase):
    def test_valid_guaranteed_analysis(self):
        data = {
            "title": "Basic Analysis",
            "nutrients": [{"value": 12.5, "unit": "mg", "nutrient": "Calcium"}],
            "is_minimal": True,
        }
        analysis = GuaranteedAnalysis.model_validate(data)
        self.assertEqual(analysis.title, "Basic Analysis")
        self.assertEqual(len(analysis.nutrients), 1)
        self.assertTrue(analysis.is_minimal)

    def test_valid_empty_nutrients_list(self):
        data = {"title": "Empty Nutrients", "nutrients": [], "is_minimal": False}
        analysis = GuaranteedAnalysis.model_validate(data)
        self.assertEqual(analysis.title, "Empty Nutrients")
        self.assertEqual(len(analysis.nutrients), 0)
        self.assertFalse(analysis.is_minimal)

    def test_valid_none_title(self):
        data = {
            "title": None,
            "nutrients": [{"value": 5.0, "unit": "g", "nutrient": "Iron"}],
            "is_minimal": True,
        }
        analysis = GuaranteedAnalysis.model_validate(data)
        self.assertIsNone(analysis.title)
        self.assertEqual(len(analysis.nutrients), 1)
        self.assertTrue(analysis.is_minimal)

    def test_valid_none_is_minimal(self):
        data = {
            "title": "No Minimal",
            "nutrients": [{"value": 3.2, "unit": "g", "nutrient": "Vitamin C"}],
            "is_minimal": None,
        }
        analysis = GuaranteedAnalysis.model_validate(data)
        self.assertEqual(analysis.title, "No Minimal")
        self.assertEqual(len(analysis.nutrients), 1)
        self.assertIsNone(analysis.is_minimal)

    def test_valid_none_all_fields(self):
        data = {"title": None, "nutrients": [], "is_minimal": None}
        analysis = GuaranteedAnalysis.model_validate(data)
        self.assertIsNone(analysis.title)
        self.assertEqual(len(analysis.nutrients), 0)
        self.assertIsNone(analysis.is_minimal)

    def test_invalid_nutrients_not_a_list(self):
        data = {
            "title": "Invalid Nutrients",
            "nutrients": "invalid",
            "is_minimal": True,
        }
        with self.assertRaises(ValidationError):
            GuaranteedAnalysis.model_validate(data)

    def test_invalid_is_minimal_type(self):
        data = {"title": "Wrong Type", "nutrients": [], "is_minimal": "invalid"}
        with self.assertRaises(ValidationError):
            GuaranteedAnalysis.model_validate(data)


class TestLabelData(TestCase):
    def setUp(self):
        self.base_data = {
            "organizations": [
                {
                    "name": "AgriCorp",
                    "address": "123 Farm St",
                    "website": "https://agricorp.com",
                    "phone_number": "+1 416-555-1234",
                }
            ],
            "fertiliser_name": "Super Grow",
            "registration_number": [
                {"identifier": "1234567A", "type": "fertilizer_product"}
            ],
            "lot_number": "LOT123",
            "weight": [{"value": 50.0, "unit": "kg"}],
            "density": {"value": 1.2, "unit": "g/cm3"},
            "volume": {"value": 100.0, "unit": "L"},
            "npk": "10-5-10",
            "guaranteed_analysis_en": {
                "title": "Analysis EN",
                "nutrients": [],
                "is_minimal": True,
            },
            "guaranteed_analysis_fr": {
                "title": "Analysis FR",
                "nutrients": [],
                "is_minimal": False,
            },
            "cautions_en": ["Keep out of reach of children"],
            "cautions_fr": ["Tenir hors de portée des enfants"],
            "instructions_en": ["Mix with water before use."],
            "instructions_fr": ["Mélanger avec de l'eau avant utilisation."],
            "ingredients_en": [{"value": 5.0, "unit": "g", "nutrient": "Nitrogen"}],
            "ingredients_fr": [{"value": 3.0, "unit": "g", "nutrient": "Phosphorus"}],
        }

    def test_valid_label_data(self):
        label_data = LabelData.model_validate(self.base_data)
        self.assertEqual(label_data.fertiliser_name, "Super Grow")

    def test_valid_empty_lists(self):
        data = self.base_data.copy()
        data["organizations"] = []
        data["registration_number"] = []
        data["weight"] = []
        data["instructions_en"] = []
        data["cautions_en"] = []
        data["cautions_fr"] = []
        label_data = LabelData.model_validate(data)
        self.assertEqual(len(label_data.organizations), 0)
        self.assertEqual(len(label_data.registration_number), 0)
        self.assertEqual(len(label_data.weight), 0)
        self.assertEqual(len(label_data.instructions_en), 0)
        self.assertEqual(len(label_data.cautions_en), 0)
        self.assertEqual(len(label_data.cautions_fr), 0)

    def test_valid_none_fields(self):
        data = self.base_data.copy()
        data["lot_number"] = None
        data["density"] = None
        data["volume"] = None
        data["npk"] = None
        data["cautions_en"] = None
        data["cautions_fr"] = None
        label_data = LabelData.model_validate(data)
        self.assertIsNone(label_data.lot_number)
        self.assertIsNone(label_data.density)
        self.assertIsNone(label_data.volume)
        self.assertIsNone(label_data.npk)
        self.assertIsNone(label_data.cautions_en)
        self.assertIsNone(label_data.cautions_fr)

    def test_invalid_npk_format(self):
        data = self.base_data.copy()
        data["npk"] = "10-5"
        with self.assertRaises(ValidationError):
            LabelData.model_validate(data)

    def test_invalid_registration_number_type(self):
        data = self.base_data.copy()
        data["registration_number"] = "invalid"
        with self.assertRaises(ValidationError):
            LabelData.model_validate(data)

    def test_invalid_organizations_type(self):
        data = self.base_data.copy()
        data["organizations"] = "invalid"
        with self.assertRaises(ValidationError):
            LabelData.model_validate(data)

    def test_invalid_weight_type(self):
        data = self.base_data.copy()
        data["weight"] = "invalid"
        with self.assertRaises(ValidationError):
            LabelData.model_validate(data)
