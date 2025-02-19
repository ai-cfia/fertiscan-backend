from unittest import TestCase
from uuid import uuid4

from app.models.inspections import (
    Inspection,
    InspectionResponse,
    OrganizationInformation,
    ProductInformation,
    RegistrationNumbers,
)


class TestOrganizationInformation(TestCase):
    def test_valid_data(self):
        data = {
            "id": str(uuid4()),
            "name": "Test Org",
            "address": "123 Test St",
            "website": "https://test.org",
            "phone_number": "+14165551234",
            "edited": True,
            "is_main_contact": False,
        }
        org = OrganizationInformation.model_validate(data)
        self.assertEqual(org.name, "Test Org")
        self.assertTrue(org.edited)

    def test_missing_optional_fields(self):
        data = {"name": "Minimal Org"}
        org = OrganizationInformation.model_validate(data)
        self.assertEqual(org.name, "Minimal Org")
        self.assertIsNone(org.id)
        self.assertIsNone(org.phone_number)

    def test_invalid_uuid(self):
        data = {"id": "invalid-uuid"}
        with self.assertRaises(ValueError):
            OrganizationInformation.model_validate(data)

    def test_invalid_phone_number(self):
        data = {"phone_number": "invalid-phone"}
        with self.assertRaises(ValueError):
            OrganizationInformation.model_validate(data)


class TestRegistrationNumbers(TestCase):
    def test_valid_registration_number(self):
        data = {"registration_number": "1234567A"}
        reg_num = RegistrationNumbers.model_validate(data)
        self.assertEqual(reg_num.registration_number, "1234567A")

    def test_invalid_registration_number(self):
        data = {"registration_number": "12345X"}  # Wrong format
        with self.assertRaises(ValueError):
            RegistrationNumbers.model_validate(data)

    def test_missing_registration_number(self):
        data = {}
        reg_num = RegistrationNumbers.model_validate(data)
        self.assertIsNone(reg_num.registration_number)

    def test_extra_fields_ignored(self):
        data = {"registration_number": "7654321B", "extra_field": "ignored"}
        reg_num = RegistrationNumbers.model_validate(data)
        self.assertEqual(reg_num.registration_number, "7654321B")
        self.assertFalse(hasattr(reg_num, "extra_field"))


class TestProductInformation(TestCase):
    def test_valid_product(self):
        data = {
            "name": "Test Product",
            "label_id": str(uuid4()),
            "lot_number": "LOT123",
            "npk": "10-5-20",
            "warranty": "1 year",
            "n": 10.0,
            "p": 5.0,
            "k": 20.0,
            "verified": True,
            "registration_numbers": [{"registration_number": "1234567A"}],
            "record_keeping": False,
        }
        product = ProductInformation.model_validate(data)
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.npk, "10-5-20")
        self.assertTrue(product.verified)

    def test_invalid_npk_format(self):
        data = {"npk": "invalid-npk"}
        with self.assertRaises(ValueError):
            ProductInformation.model_validate(data)

    def test_missing_optional_fields(self):
        data = {"name": "Minimal Product"}
        product = ProductInformation.model_validate(data)
        self.assertEqual(product.name, "Minimal Product")
        self.assertIsNone(product.label_id)
        self.assertEqual(product.registration_numbers, [])

    def test_invalid_label_id(self):
        data = {"label_id": "invalid-uuid"}
        with self.assertRaises(ValueError):
            ProductInformation.model_validate(data)

    def test_empty_registration_numbers(self):
        data = {"registration_numbers": []}
        product = ProductInformation.model_validate(data)
        self.assertEqual(product.registration_numbers, [])


class TestInspection(TestCase):
    def setUp(self):
        self.data = {
            "inspection_id": str(uuid4()),
            "inspector_id": str(uuid4()),
            "inspection_comment": "All good",
            "verified": True,
            "organizations": [{"name": "Test Org"}],
            "product": {"name": "Test Product", "npk": "10-5-20"},
            "cautions": {"text": "Handle with care"},
            "instructions": {"text": "Use as directed"},
            "guaranteed_analysis": {"values": [{"name": "Nitrogen", "value": 10.0}]},
            "ingredients": {"values": [{"name": "Ingredient A", "amount": 5.0}]},
            "picture_set_id": str(uuid4()),
            "folder_id": str(uuid4()),
            "container_id": str(uuid4()),
        }

    def test_valid_inspection(self):
        inspection = Inspection.model_validate(self.data)
        self.assertEqual(inspection.inspection_comment, "All good")
        self.assertTrue(inspection.verified)
        self.assertEqual(inspection.product.name, "Test Product")

    def test_missing_optional_fields(self):
        self.data.pop("inspection_id")
        self.data.pop("inspector_id")
        self.data.pop("organizations")
        self.data["organizations"] = []
        inspection = Inspection.model_validate(self.data)
        self.assertIsNone(inspection.inspection_id)
        self.assertIsNone(inspection.inspector_id)
        self.assertEqual(inspection.organizations, [])

    def test_invalid_inspection_id(self):
        self.data["inspection_id"] = "invalid-uuid"
        with self.assertRaises(ValueError):
            Inspection.model_validate(self.data)

    def test_invalid_picture_set_id(self):
        self.data["picture_set_id"] = "invalid-uuid"
        with self.assertRaises(ValueError):
            Inspection.model_validate(self.data)

    def test_empty_organizations(self):
        self.data["organizations"] = []
        inspection = Inspection.model_validate(self.data)
        self.assertEqual(inspection.organizations, [])


class TestInspectionResponse(TestCase):
    def setUp(self):
        self.data = {
            "inspection_id": str(uuid4()),
            "inspector_id": str(uuid4()),
            "inspection_comment": "All good",
            "verified": True,
            "organizations": [{"name": "Test Org"}],
            "product": {"name": "Test Product", "npk": "10-5-20"},
            "cautions": {"text": "Handle with care"},
            "instructions": {"text": "Use as directed"},
            "guaranteed_analysis": {"values": [{"name": "Nitrogen", "value": 10.0}]},
            "ingredients": {"values": [{"name": "Ingredient A", "amount": 5.0}]},
            "picture_set_id": str(uuid4()),
            "folder_id": str(uuid4()),
            "container_id": str(uuid4()),
        }

    def test_valid_inspection_response(self):
        response = InspectionResponse.model_validate(self.data)
        self.assertEqual(str(response.inspection_id), self.data["inspection_id"])
        self.assertEqual(response.product.name, "Test Product")

    def test_missing_inspection_id(self):
        self.data.pop("inspection_id")
        with self.assertRaises(ValueError):
            InspectionResponse.model_validate(self.data)

    def test_invalid_inspection_id(self):
        self.data["inspection_id"] = "invalid-uuid"
        with self.assertRaises(ValueError):
            InspectionResponse.model_validate(self.data)
