import os
import unittest
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from pipeline import FertilizerInspection

from app.main import app


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up the environment variable to indicate testing mode
        os.environ["TESTING"] = "True"

    def setUp(self):
        # Generate unique IDs and values for each test run
        self.subtype_id = uuid.uuid4()
        self.type_en = uuid.uuid4().hex
        self.type_fr = uuid.uuid4().hex

    def test_rollbacks(self):
        # Test inserting a new subtype
        with TestClient(app) as client:
            response = client.post(
                "/subtypes",
                params={
                    "id": self.subtype_id,
                    "type_en": self.type_en,
                    "type_fr": self.type_fr,
                },
            )
            # Check if the POST request was successful
            self.assertEqual(response.status_code, 200)

            # Validate the response content
            results = response.json().get("message")
            self.assertIsNotNone(results)

            # Check if the inserted subtype matches the expected values
            response = client.get(f"/subtypes/{self.subtype_id}")
            self.assertEqual(response.status_code, 200)
            # Validate the response content
            results = response.json().get("message")
            self.assertIsNotNone(results)
            self.assertEqual(results[0], str(self.subtype_id))
            self.assertEqual(results[1], self.type_fr)
            self.assertEqual(results[2], self.type_en)

        # Test if the subtype was rolled back (i.e., not found)
        with TestClient(app) as client:
            response = client.get(f"/{self.subtype_id}")
            # Expect a 404 status code, indicating that the subtype was not found
            self.assertEqual(response.status_code, 404)

    @patch("app.main.extract_data")
    def test_analyze_document(self, mock_extract_data):
        mock_inspection_data = {
            "company_name": "Test Company",
            "fertiliser_name": "Mock Fertilizer",
            "registration_number": "REG123",
        }
        mock_inspection = FertilizerInspection.model_validate(mock_inspection_data)
        mock_extract_data.return_value = mock_inspection

        # Mock files for testing
        file_content_1 = b"Sample content 1"
        file_content_2 = b"Sample content 2"

        files = [
            ("files", ("file1.txt", file_content_1, "text/plain")),
            ("files", ("file2.txt", file_content_2, "text/plain")),
        ]

        with TestClient(app) as client:
            response = client.post("/analyze", files=files)

            # Check if the request was successful
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            validated_inspection = FertilizerInspection.model_validate(response_data)

            # Compare fields
            self.assertEqual(
                validated_inspection.company_name, mock_inspection.company_name
            )
            self.assertEqual(
                validated_inspection.fertiliser_name, mock_inspection.fertiliser_name
            )
            self.assertEqual(
                validated_inspection.registration_number,
                mock_inspection.registration_number,
            )
