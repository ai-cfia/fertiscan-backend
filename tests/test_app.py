import base64
import os
import unittest
import uuid
import json

from io import BytesIO
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import File

import requests
from azure.storage.blob import BlobServiceClient

from app import app, connection_manager
from pipeline import FertilizerInspection

class APITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup credentials and headers
        cls.username = "test-user-10"
        cls.password = "password1"
        encoded_credentials = cls.credentials(cls.username, cls.password)

        cls.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }

        # Fetch and save the JSON data in setUpClass
        with requests.get(
            "https://raw.githubusercontent.com/ai-cfia/fertiscan-pipeline/main/expected.json"
        ) as response:
            cls.analysis_json = response.json()

    @classmethod
    def credentials(cls, username, password) -> str:
        credentials = f"{username}:{password}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    def setUp(self):
        app.testing = True
        self.client = TestClient(app)
        self.client.headers.update(self.headers)
        self.client.post(
            "/signup",
            headers={
                **self.headers,
                "Authorization": f'Basic {self.credentials(self.username, self.password)}',
            },
        )

    def tearDown(self):
        connection_manager.rollback()
        connection_manager.put()

    def test_health(self):
        response = self.client.get("/health", headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_conn(self):
        # Test the database connection using ConnectionManager
        try:
            with connection_manager as manager:
                with manager.get_cursor() as cursor:
                    cursor.execute(
                        f"""SELECT 1 from "{os.getenv("FERTISCAN_SCHEMA")}".users"""
                    )
                    cursor.fetchall()
        except Exception as e:
            self.fail(f"Database connection failed: {str(e)}")

    def test_blob_conn(self):
        FERTISCAN_STORAGE_URL = os.getenv("FERTISCAN_STORAGE_URL")
        self.assertIsNotNone(
            FERTISCAN_STORAGE_URL,
            "FERTISCAN_STORAGE_URL environment variable is not set.",
        )
        blob_service_client = BlobServiceClient.from_connection_string(
            FERTISCAN_STORAGE_URL
        )
        service_properties = blob_service_client.get_service_properties()
        self.assertIsNotNone(
            service_properties, "Failed to retrieve service properties."
        )

    def test_signup_missing_username(self):
        response = self.client.post(
            "/signup",
            headers={
            **self.headers,
            "Authorization": f'Basic {self.credentials("", self.password)}',
            },
        )
        self.assertEqual(response.status_code, 400, response.json())

    # def test_signup(self):
    #     username = str(uuid.uuid4())
    #     response = self.client.post(
    #         "/signup",
    #         headers={
    #         **self.headers,
    #         "Authorization": f'Basic {self.credentials(username, self.password)}',
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         },
    #     )
    #     self.assertEqual(response.status_code, 201, response.json())

    def test_login_missing_username(self):
        response = self.client.post(
            "/login",
            headers={
            **self.headers,
            "Authorization": f'Basic {self.credentials("", self.password)}',
            },
        )
        self.assertEqual(response.status_code, 400, response.json())

    # def test_login_unknown_username(self):
    #     username = str(uuid.uuid4())
    #     response = self.client.post(
    #         "/login",
    #         headers={
    #         **self.headers,
    #         "Authorization": f"Basic {self.credentials(username, self.password)}",
    #         },
    #     )
    #     self.assertEqual(response.status_code, 401, response.json())

    # def test_login(self):
    #     response = self.client.post(
    #         "/login",
    #         headers=self.headers,
    #     )
    #     self.assertEqual(response.status_code, 200, response.json())

    def test_create_inspection_no_inspection(self):
        response = self.client.post("/inspections", files=[])
        self.assertEqual(response.status_code, 422, response.json())

    # def test_create_inspection(self):
    #     response = self.client.post(
    #         "/inspections/",
    #         data={
    #             "inspection": self.analysis_json,
    #         },
    #     )
    #     self.assertEqual(response.status_code, 201, response.content)
    #     self.assertIn("inspection_id", response.get_json(), response.json())

    # def test_update_inspection_fake_id(self):
    #     fake_inspection_id = str(uuid.uuid4())

    #     response = self.client.put(
    #         f"/inspections/{fake_inspection_id}",
    #         json=self.analysis_json,
    #     )
    #     self.assertEqual(response.status_code, 500, response.json())
    #     self.assertIn("error", response.json(), response.json())

    def test_update_empty_inspection(self):
        inspection_id = str(uuid.uuid4())
        response = self.client.put(
            f"/inspections/{inspection_id}", json = {}
        )
        self.assertEqual(response.status_code, 500, response.json())

    # def test_update_inspection(self):
    #     # Create a new inspection first
    #     response = self.client.post(
    #         "/inspections", headers=self.headers, json=self.analysis_json
    #     )
    #     self.assertEqual(response.status_code, 201, response.json())

    #     # Use the response data from the creation for the update
    #     update_data = response.get_json()
    #     inspection_id = update_data["inspection_id"]

    #     response = self.client.put(
    #         f"/inspections/{inspection_id}", headers=self.headers, json=update_data
    #     )
    #     self.assertEqual(response.status_code, 200, response.get_json())

    def test_get_inspection_from_unknown_user(self):
        username = str(uuid.uuid4())
        response = self.client.get(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 500, response.json())

    # def test_get_inspection(self):
    #     response = self.client.get(
    #         "/inspections",
    #         # headers=self.headers,
    #     )
    #     self.assertEqual(response.status_code, 200, response.json())

    # def test_get_inspection_by_id(self):
    #     # Create a new inspection first
    #     response = self.client.post(
    #         "/inspections", headers=self.headers, json=self.analysis_json
    #     )
    #     self.assertEqual(response.status_code, 201, response.json())

    #     # Use the response data from the creation for the update
    #     update_data = response.get_json()
    #     inspection_id = update_data["inspection_id"]

    #     response = self.client.get(
    #         f"/inspections/{inspection_id}",
    #         headers=self.headers,
    #     )
    #     self.assertEqual(response.status_code, 200, response.json())

    def test_analyze_document_no_files(self):
        response = self.client.post("/analyze", headers=self.headers)
        self.assertEqual(response.status_code, 422, response.json())

    def test_analyze_invalid_document(self):
        # Create a BytesIO object to simulate file upload (empty or invalid content)
        invalid_file = BytesIO(b"")  # Empty content to simulate invalid file
        invalid_file.name = 'invalid_file.png'  # Typically, a .txt might be unsupported for an image-based analysis API

        # Send the request with the invalid file
        response = self.client.post(
            "/analyze",
            files={"files": ("invalid_file.jpg", invalid_file, "image/png")},
        )

        # Document Intelligence throws an error
        self.assertEqual(response.status_code, 500, response.json())

    @patch("app.gpt.create_inspection")
    @patch("app.ocr.extract_text")
    def test_analyze_document_gpt_error(self, mock_ocr, mock_gpt):
        mock_ocr.return_value = MagicMock(content="OCR result")
        mock_gpt.side_effect = Exception("GPT error")

        # Create a BytesIO object to simulate file upload (empty or invalid content)
        invalid_file = BytesIO(b"")  # Empty content to simulate invalid file
        invalid_file.name = 'invalid_file.png'  # Typically, a .txt might be unsupported for an image-based analysis API

        response = self.client.post(
            "/analyze",
            files={"files": ("invalid_file.jpg", invalid_file, "image/png")},
        )

        self.assertEqual(response.status_code, 500, response.json())
        
    # def test_get_inspection_by_id(self):
    #     # Create a new inspection first
    #     response = self.client.post(
    #         "/inspections", headers=self.headers, content=self.analysis_json
    #     )
    #     self.assertEqual(response.status_code, 201, response.json())

    #     # Use the response data from the creation for the retrieval
    #     created_inspection = response.json()
    #     inspection_id = created_inspection["inspection_id"]

    #     response = self.client.get(
    #         f"/inspections/{inspection_id}",
    #         headers=self.headers,
    #     )
    #     self.assertEqual(response.status_code, 200, response.json())

    def test_get_inspection_by_invalid_id(self):
        fake_inspection_id = str(uuid.uuid4())

        response = self.client.get(
            f"/inspections/{fake_inspection_id}",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 500, response.json())
        self.assertIn("detail", response.json())

if __name__ == "__main__":
    unittest.main()
