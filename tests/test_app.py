import base64
import os
import tempfile
import unittest
import uuid
from unittest.mock import patch

import requests
from fastapi.testclient import TestClient
from pipeline import FertilizerInspection

from app.main import app
from app.models.label_data import LabelData


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup credentials and headers
        cls.username = "test-user-1"
        cls.password = "password1"
        encoded_credentials = cls.credentials(cls.username, cls.password)

        cls.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }

        os.environ["TESTING"] = "True"

        # Fetch and save the JSON data in setUpClass
        with requests.get(
            "https://raw.githubusercontent.com/ai-cfia/fertiscan-pipeline/main/expected.json"
        ) as response:
            cls.analysis_json = response.json()

    @classmethod
    def credentials(cls, username, password) -> str:
        credentials = f"{username}:{password}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    def test_health_check(self):
        with TestClient(app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(response.json(), {"status": "ok"})

    def test_user_signup_missing_username(self):
        with TestClient(app) as client:
            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f'Basic {self.credentials("", self.password)}',
                },
            )
            self.assertEqual(response.status_code, 400, response.json())

    def test_user_signup_conflict(self):
        with TestClient(app) as client:
            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 201, response.json())

            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 409, response.json())

    def test_user_signup(self):
        with TestClient(app) as client:
            username = str(uuid.uuid4())
            response = client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 201, response.json())

    def test_user_login_missing_username(self):
        with TestClient(app) as client:
            response = client.post(
                "/login",
                headers={
                    **self.headers,
                    "Authorization": f'Basic {self.credentials("", self.password)}',
                },
            )
            self.assertEqual(response.status_code, 400, response.json())

    def test_user_login(self):
        with TestClient(app) as client:
            client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            response = client.post(
                "/login",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 200, response.json())

    def test_user_login_not_found(self):
        new_username = uuid.uuid4().hex
        with TestClient(app) as client:
            response = client.post(
                "/login",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(new_username, self.password)}",
                },
            )
            self.assertEqual(response.status_code, 401, response.json())

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
            validated_inspection = LabelData.model_validate(response_data)

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

    @patch("app.main.extract_data")
    def test_analyze_empty_file(self, mock_extract_data):
        """Test analyze_document with an empty file that triggers ResponseValidationError"""
        mock_extract_data.return_value = None

        files = [("files", ("empty.txt", b"", "text/plain"))]

        with TestClient(app) as client:
            response = client.post("/analyze", files=files)
            self.assertEqual(response.status_code, 422)

    @patch("app.main.extract_data")
    def test_analyze_file_list_with_empty_files(self, mock_extract_data):
        """Test analyze_document with a file list containing empty files"""
        mock_inspection_data = {
            "company_name": "Test Company",
            "fertiliser_name": "Mock Fertilizer",
            "registration_number": "REG123",
        }
        mock_inspection = FertilizerInspection.model_validate(mock_inspection_data)
        mock_extract_data.return_value = mock_inspection

        files = [
            ("files", ("file1.txt", b"Sample content", "text/plain")),
            ("files", ("empty.txt", b"", "text/plain")),
        ]

        with TestClient(app) as client:
            response = client.post("/analyze", files=files)
            self.assertEqual(response.status_code, 422)

    @patch("app.main.extract_data")
    def test_analyze_empty_file_list(self, mock_extract_data):
        """Test analyze_document with an empty file list"""
        mock_extract_data.return_value = None

        files = []

        with TestClient(app) as client:
            response = client.post("/analyze", files=files)
            self.assertEqual(response.status_code, 422)

    @patch("app.constants.UPLOAD_FOLDER", new_callable=tempfile.TemporaryDirectory)
    def test_analyze_integration(self, temp_upload_folder):
        with TestClient(app) as client:
            # Read the image file from the same directory
            with open("tests/label.png", "rb") as img_file:
                image_content = img_file.read()

            files = [("files", ("label.png", image_content, "image/png"))]

            response = client.post("/analyze", files=files)

            # Check if the request was successful
            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            LabelData.model_validate(response_data)

    def test_get_inspections_success(self):
        with TestClient(app) as client:
            client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )

            response = client.get(
                "/inspections",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )

            self.assertEqual(response.status_code, 200)
            self.assertListEqual(response.json(), [])

    def test_get_inspections_unauthorized(self):
        with TestClient(app) as client:
            # Attempt to access the /inspections endpoint without authentication headers
            response = client.get("/inspections")

            # Verify the response status code is 401 Unauthorized
            self.assertEqual(response.status_code, 401)

    def test_get_inspections_with_invalid_auth(self):
        with TestClient(app) as client:
            # Generate an invalid username using a random UUID hex
            invalid_username = uuid.uuid4().hex
            invalid_password = "wrongpassword"

            # Attempt to access the /inspections endpoint with invalid credentials
            response = client.get(
                "/inspections",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(invalid_username, invalid_password)}",
                },
            )

            # Verify the response status code is 401 Unauthorized
            self.assertEqual(response.status_code, 401)

    def test_get_inspections_missing_auth_credentials(self):
        with TestClient(app) as client:
            # Attempt to access the /inspections endpoint with an empty username
            response = client.get(
                "/inspections",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials('', self.password)}",
                },
            )

            # Verify the response status code is 400 Bad Request
            self.assertEqual(response.status_code, 400)

    def test_get_inspection_not_found(self):
        with TestClient(app) as client:
            client.post(
                "/signup",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )

            response = client.get(
                f"/inspections/{uuid.uuid4()}",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(self.username, self.password)}",
                },
            )

            self.assertEqual(response.status_code, 404)

    def test_get_inspection_unauthorized(self):
        with TestClient(app) as client:
            response = client.get("/inspections/1")
            self.assertEqual(response.status_code, 401)

    def test_get_inspection_bad_auth(self):
        with TestClient(app) as client:
            response = client.get(
                "/inspections/1",
                headers={
                    **self.headers,
                    "Authorization": f"Basic {self.credentials(uuid.uuid4().hex, 'badpass')}",
                },
            )
            self.assertEqual(response.status_code, 401)

    # TODO: Implement once we have post inspections is implemented
    # def test_get_inspection_success(self):
    #     with TestClient(app) as client:
    #         client.post(
    #             "/signup",
    #             headers={
    #                 **self.headers,
    #                 "Authorization": f"Basic {self.credentials(self.username, self.password)}",
    #             },
    #         )
