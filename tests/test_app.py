import base64
import json
import os
import tempfile
import unittest
import uuid
from io import BytesIO
from unittest.mock import patch

import requests
from azure.storage.blob import ContainerClient
from fastapi.testclient import TestClient
from pipeline import FertilizerInspection

from app.config import Settings, configure
from app.main import app
from app.models.inspections import Inspection
from app.models.label_data import LabelData
from app.models.users import User


class TestAPI(unittest.TestCase):
    @classmethod
    def credentials(cls, username, password) -> str:
        credentials = f"{username}:{password}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    @classmethod
    def delete_containers(cls, user_id):
        if not user_id:
            return
        container_client = ContainerClient.from_connection_string(
            os.getenv("FERTISCAN_STORAGE_URL"), container_name=f"user-{user_id}"
        )
        if container_client.exists():
            container_client.delete_container()

    @classmethod
    def setUpClass(cls):
        cls.username = uuid.uuid4().hex
        cls.password = "password1"
        encoded_credentials = cls.credentials(cls.username, cls.password)

        cls.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        }

        cls.files = [
            ("files", ("image1.png", BytesIO(b"fake_image_data_1"), "image/png")),
            ("files", ("image2.png", BytesIO(b"fake_image_data_2"), "image/png")),
        ]

        os.environ["TESTING"] = "True"

        # Fetch and save the JSON data in setUpClass
        with requests.get(
            "https://raw.githubusercontent.com/ai-cfia/fertiscan-pipeline/main/expected.json"
        ) as response:
            cls.label_data = response.json()

        temp = tempfile.TemporaryDirectory()
        settings = Settings(upload_folder=temp.name)
        configure(app, settings)
        app.connection_manager.pool.open()

    @classmethod
    def tearDownClass(cls):
        app.connection_manager.pool.close()

    def setUp(self):
        self.client = TestClient(app)
        response = self.client.post(
            "/signup",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
        )
        self.user = User.model_validate(response.json())

    def tearDown(self):
        app.connection_manager.rollback()
        self.delete_containers(self.user.id)

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {"status": "ok"})

    def test_user_signup_missing_username(self):
        response = self.client.post(
            "/signup",
            headers={
                **self.headers,
                "Authorization": f'Basic {self.credentials("", self.password)}',
            },
        )
        self.assertEqual(response.status_code, 400, response.json())

    def test_user_signup_conflict(self):
        response = self.client.post(
            "/signup",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 409, response.json())

    def test_user_login_missing_username(self):
        response = self.client.post(
            "/login",
            headers={
                **self.headers,
                "Authorization": f'Basic {self.credentials("", self.password)}',
            },
        )
        self.assertEqual(response.status_code, 400, response.json())

    def test_user_login(self):
        response = self.client.post(
            "/login",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 200, response.json())

    def test_user_login_not_found(self):
        new_username = uuid.uuid4().hex
        response = self.client.post(
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

        file_content_1 = b"Sample content 1"
        file_content_2 = b"Sample content 2"

        files = [
            ("files", ("file1.txt", file_content_1, "text/plain")),
            ("files", ("file2.txt", file_content_2, "text/plain")),
        ]

        response = self.client.post("/analyze", files=files)
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        validated_inspection = LabelData.model_validate(response_data)
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
        response = self.client.post("/analyze", files=files)
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
        response = self.client.post("/analyze", files=files)
        self.assertEqual(response.status_code, 422)

    @patch("app.main.extract_data")
    def test_analyze_empty_file_list(self, mock_extract_data):
        """Test analyze_document with an empty file list"""
        mock_extract_data.return_value = None
        files = []
        response = self.client.post("/analyze", files=files)
        self.assertEqual(response.status_code, 422)

    def test_analyze_integration(self):
        with open("tests/label.png", "rb") as img_file:
            image_content = img_file.read()
        files = [("files", ("label.png", image_content, "image/png"))]
        response = self.client.post("/analyze", files=files)
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        LabelData.model_validate(response_data)

    def test_get_inspections_success(self):
        response = self.client.get(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertListEqual(response.json(), [])

    def test_get_inspections_unauthorized(self):
        response = self.client.get("/inspections")
        self.assertEqual(response.status_code, 401)

    def test_get_inspections_with_invalid_auth(self):
        invalid_username = uuid.uuid4().hex
        invalid_password = "wrongpassword"
        response = self.client.get(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(invalid_username, invalid_password)}",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_get_inspections_missing_auth_credentials(self):
        response = self.client.get(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials('', self.password)}",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_get_inspection_not_found(self):
        response = self.client.get(
            f"/inspections/{uuid.uuid4()}",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_get_inspection_unauthorized(self):
        response = self.client.get("/inspections/1")
        self.assertEqual(response.status_code, 401)

    def test_get_inspection_bad_auth(self):
        response = self.client.get(
            "/inspections/1",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(uuid.uuid4().hex, 'badpass')}",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_get_inspection_success(self):
        response = self.client.post(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
            data={"label_data": json.dumps(self.label_data)},
            files=self.files,
        )
        self.assertEqual(response.status_code, 200)
        inspection = Inspection.model_validate(response.json())
        # remove the inspection_comment field for comparison
        inspection.inspection_comment = None
        response = self.client.get(
            f"/inspections/{inspection.inspection_id}",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
        )
        self.assertEqual(response.status_code, 200)
        fetched_inspection = Inspection.model_validate(response.json())
        self.assertEqual(inspection, fetched_inspection)

    def test_create_inspection_success(self):
        response = self.client.post(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(self.username, self.password)}",
            },
            data={"label_data": json.dumps(self.label_data)},
            files=self.files,
        )
        self.assertEqual(response.status_code, 200)
        Inspection.model_validate(response.json())

    def test_create_inspection_unauthorized(self):
        response = self.client.post(
            "/inspections",
            data={"label_data": json.dumps({"company_name": "string"})},
            files=[("files", ("image1.png", BytesIO(b"fake_image_data"), "image/png"))],
        )

        self.assertEqual(response.status_code, 401)

    def test_create_inspection_with_invalid_auth(self):
        invalid_username = uuid.uuid4().hex
        invalid_password = "wrongpassword"
        response = self.client.post(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials(invalid_username, invalid_password)}",
            },
            data={"label_data": json.dumps({"company_name": "string"})},
            files=[("files", ("image1.png", BytesIO(b"fake_image_data"), "image/png"))],
        )
        self.assertEqual(response.status_code, 401)

    def test_create_inspection_missing_auth_credentials(self):
        response = self.client.post(
            "/inspections",
            headers={
                **self.headers,
                "Authorization": f"Basic {self.credentials('', self.password)}",
            },
            data={"label_data": json.dumps({"company_name": "string"})},
            files=[("files", ("image1.png", BytesIO(b"fake_image_data"), "image/png"))],
        )
        self.assertEqual(response.status_code, 400)
