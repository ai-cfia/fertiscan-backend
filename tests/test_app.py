import base64
import os
import unittest
import uuid
from io import BytesIO
from unittest.mock import MagicMock, patch

import requests
from azure.storage.blob import BlobServiceClient

from app import app, connection_manager

class APITestCase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Setup credentials and headers
        cls.username = "test-user-2"
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

    async def asyncSetUp(self):
        app.testing = True
        self.client = app.test_client(use_cookies=False)

    async def asyncTearDown(self):
        connection_manager.rollback()
        connection_manager.put()

    async def test_health(self):
        response = await self.client.get("/health", headers=self.headers)
        self.assertEqual(response.status_code, 200)

    async def test_conn(self):
        # Test the database connection using ConnectionManager
        try:
            with connection_manager as manager:
                async with manager.get_cursor() as cursor:
                    await cursor.execute(
                        f"""SELECT 1 from "{os.getenv("FERTISCAN_SCHEMA")}".users"""
                    )
                    await cursor.fetchall()
        except Exception as e:
            self.fail(f"Database connection failed: {str(e)}")

    async def test_blob_conn(self):
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

    async def test_signup_missing_username(self):
        response = await self.client.post(
            "/signup",
            headers={
                **self.headers,
                "Authorization": f'Basic {self.credentials("", self.password)}',
            },
        )
        self.assertEqual(response.status_code, 400, await response.json)

    async def test_signup(self):
        username = str(uuid.uuid4())
        response = await self.client.post(
            "/signup",
            headers={
                **self.headers,
                "Authorization": f'Basic {self.credentials(username, self.password)}',
            },
        )
        self.assertEqual(response.status_code, 201, await response.json)

    async def test_login_missing_username(self):
        response = await self.client.post(
            "/login",
            headers={
                **self.headers,
                "Authorization": f'Basic {self.credentials("", self.password)}',
            },
        )
        self.assertEqual(response.status_code, 400, await response.json)

    async def test_login_unknown_username(self):
        username = str(uuid.uuid4())
        response = await self.client.post(
            "/login",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 401, await response.json)

    async def test_login(self):
        response = await self.client.post(
            "/login",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, await response.json)

    async def test_create_empty_inspection(self):
        response = await self.client.post("/inspections", headers=self.headers)
        self.assertEqual(response.status_code, 500, await response.json)

    async def test_create_inspection(self):
        response = await self.client.post(
            "/inspections", headers=self.headers, json=self.analysis_json
        )
        self.assertEqual(response.status_code, 201, await response.get_json())
        self.assertIn("inspection_id", await response.get_json(), await response.get_json())

    async def test_update_inspection_fake_id(self):
        fake_inspection_id = str(uuid.uuid4())

        response = await self.client.put(
            f"/inspections/{fake_inspection_id}",
            headers=self.headers,
            json=self.analysis_json,
        )
        self.assertEqual(response.status_code, 500, await response.get_json())
        self.assertIn("error", await response.get_json(), await response.get_json())

    async def test_update_empty_inspection(self):
        inspection_id = str(uuid.uuid4())
        response = await self.client.put(
            f"/inspections/{inspection_id}", headers=self.headers
        )
        self.assertEqual(response.status_code, 500, await response.get_json())

    async def test_update_inspection(self):
        # Create a new inspection first
        response = await self.client.post(
            "/inspections", headers=self.headers, json=self.analysis_json
        )
        self.assertEqual(response.status_code, 201, await response.get_json())

        # Use the response data from the creation for the update
        update_data = await response.get_json()
        inspection_id = update_data["inspection_id"]

        response = await self.client.put(
            f"/inspections/{inspection_id}", headers=self.headers, json=update_data
        )
        self.assertEqual(response.status_code, 200, await response.get_json())

    async def test_get_inspection_from_unknown_user(self):
        username = str(uuid.uuid4())
        response = await self.client.get(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 500, await response.json)

    async def test_get_inspection(self):
        response = await self.client.get(
            "/inspections",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, await response.json)

    async def test_get_inspection_by_id(self):
        # Create a new inspection first
        response = await self.client.post(
            "/inspections", headers=self.headers, json=self.analysis_json
        )
        self.assertEqual(response.status_code, 201, await response.get_json())

        # Use the response data from the creation for the update
        update_data = await response.get_json()
        inspection_id = update_data["inspection_id"]

        response = await self.client.get(
            f"/inspections/{inspection_id}",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200, await response.json)

    async def test_analyze_document_no_files(self):
        response = await self.client.post("/analyze", headers=self.headers)
        self.assertEqual(response.status_code, 400, await response.json)

    async def test_analyze_invalid_document(self):
        # Create a sample file to upload
        data = {"images": (BytesIO(b"sample image content"), "test_image.png")}

        response = await self.client.post(
            "/analyze",
            headers={**self.headers, "Content-Type": "multipart/form-data"},
            data=data
        )

        # Document Intelligence throws an error
        self.assertEqual(response.status_code, 500, await response.json)
        self.assertIn("error", await response.json)

    @patch("app.gpt.create_inspection")
    @patch("app.ocr.extract_text")
    async def test_analyze_document_gpt_error(self, mock_ocr, mock_gpt):
        mock_ocr.return_value = MagicMock(content="OCR result")
        mock_gpt.side_effect = Exception("GPT error")

        data = {"images": (BytesIO(b"sample image content"), "test_image.png")}

        response = await self.client.post(
            "/analyze",
            headers={**self.headers, "Content-Type": "multipart/form-data"},
            data=data
        )

        self.assertEqual(response.status_code, 500, await response.json)
        self.assertIn("error", await response.json)


if __name__ == "__main__":
    unittest.main()
