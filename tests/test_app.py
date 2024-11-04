import base64
import json
import unittest
import uuid
from datetime import datetime
from io import BytesIO
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from pipeline import FertilizerInspection

from app.dependencies import (
    authenticate_user,
    fetch_user,
    get_connection_manager,
    get_gpt,
    get_ocr,
    get_settings,
)
from app.exceptions import InspectionNotFoundError, UserConflictError, UserNotFoundError
from app.main import app
from app.models.inspections import Inspection, InspectionData
from app.models.label_data import LabelData
from app.models.users import User


class TestAPIMonitoring(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAPIPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

        def override_service_dep():
            return Mock()

        app.dependency_overrides.clear()
        app.dependency_overrides[get_ocr] = override_service_dep
        app.dependency_overrides[get_gpt] = override_service_dep

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
        self.assertEqual(response.status_code, 200, response.json())

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


class TestAPIUsers(unittest.TestCase):
    def credentials(self, username, password):
        credentials = f"{username}:{password}"
        return base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    def setUp(self) -> None:
        self.client = TestClient(app)

        def override_dep():
            return Mock()

        self.test_user = User(username="test_user", id=uuid.uuid4())

        app.dependency_overrides.clear()
        app.dependency_overrides[get_connection_manager] = override_dep
        app.dependency_overrides[authenticate_user] = override_dep
        app.dependency_overrides[get_settings] = override_dep
        app.dependency_overrides[fetch_user] = lambda: self.test_user

    @patch("app.main.sign_up")
    def test_signup(self, mock_sign_up):
        mock_sign_up.return_value = self.test_user
        response = self.client.post("/signup", json={"username": "test_user"})
        self.assertEqual(response.status_code, 201)
        User.model_validate(response.json())

    @patch("app.main.sign_up")
    def test_signup_existing_user(self, mock_sign_up):
        mock_sign_up.side_effect = UserConflictError()
        response = self.client.post("/signup", json={"username": "test_user"})
        self.assertEqual(response.status_code, 409)

    @patch("app.main.sign_up")
    def test_signup_bad_authentication(self, _):
        del app.dependency_overrides[authenticate_user]
        # Test with no authentication
        response = self.client.post("/signup")
        self.assertEqual(response.status_code, 401)
        # Test with empty username
        empty_username = ""
        response = self.client.post(
            "/signup",
            headers={
                "Authorization": f"Basic {self.credentials(empty_username, "password")}",
            },
        )
        self.assertEqual(response.status_code, 400)

    @patch("app.main.sign_up")
    def test_signup_authentication_success(self, mock_sign_up):
        del app.dependency_overrides[authenticate_user]
        mock_sign_up.return_value = self.test_user
        response = self.client.post(
            "/signup",
            headers={
                "Authorization": f"Basic {self.credentials("test_user", "password")}",
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_sign_in(self):
        response = self.client.post("/login")
        self.assertEqual(response.status_code, 200)
        user = User.model_validate(response.json())
        self.assertEqual(user, self.test_user)

    @patch("app.dependencies.sign_in")
    def test_sign_in_user_not_found(self, mock_sign_in):
        del app.dependency_overrides[fetch_user]
        mock_sign_in.side_effect = UserNotFoundError()
        response = self.client.post("/login")
        # if the user is not found, the response should be NOT AUTHORIZED
        self.assertEqual(response.status_code, 401)

    def test_sign_in_bad_authentication(self):
        del app.dependency_overrides[authenticate_user]
        del app.dependency_overrides[fetch_user]
        # Test with no authentication
        response = self.client.post("/login")
        self.assertEqual(response.status_code, 401)
        # Test with empty username
        empty_username = ""
        response = self.client.post(
            "/login",
            headers={
                "Authorization": f"Basic {self.credentials(empty_username, 'password')}",
            },
        )
        self.assertEqual(response.status_code, 400)

    @patch("app.dependencies.sign_in")
    def test_sign_in_authentication_success(self, mock_sign_in):
        del app.dependency_overrides[authenticate_user]
        del app.dependency_overrides[fetch_user]
        mock_sign_in.return_value = self.test_user
        response = self.client.post("/login")
        response = self.client.post(
            "/login",
            headers={
                "Authorization": f"Basic {self.credentials('test_user', 'password')}",
            },
        )
        self.assertEqual(response.status_code, 200)


class TestAPIInspections(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

        def override_dep():
            return Mock()

        self.test_user = User(username="test_user", id=uuid.uuid4())

        app.dependency_overrides.clear()
        app.dependency_overrides[get_connection_manager] = override_dep
        app.dependency_overrides[fetch_user] = lambda: self.test_user

        self.mock_inspection_data = [
            InspectionData(
                id=uuid.uuid4(),
                upload_date=datetime(2023, 1, 1),
                updated_at=datetime(2023, 1, 2),
                sample_id=uuid.uuid4(),
                picture_set_id=uuid.uuid4(),
                label_info_id=uuid.uuid4(),
                product_name="Product A",
                manufacturer_info_id=uuid.uuid4(),
                company_info_id=uuid.uuid4(),
                company_name="Company A",
            ),
            InspectionData(
                id=uuid.uuid4(),
                upload_date=datetime(2023, 1, 3),
                updated_at=datetime(2023, 1, 4),
                sample_id=uuid.uuid4(),
                picture_set_id=uuid.uuid4(),
                label_info_id=uuid.uuid4(),
                product_name="Product B",
                manufacturer_info_id=uuid.uuid4(),
                company_info_id=uuid.uuid4(),
                company_name="Company B",
            ),
        ]

        inspection_id = uuid.uuid4()
        self.sample_inspection_dict = {
            "inspection_id": str(inspection_id),
            "inspection_comment": "string",
            "verified": False,
            "company": {},
            "manufacturer": {},
            "product": {
                "name": "string",
                "label_id": "string",
                "registration_number": "string",
                "lot_number": "string",
                "metrics": {
                    "weight": [],
                    "volume": {"edited": False},
                    "density": {"edited": False},
                },
                "npk": "string",
                "warranty": "string",
                "n": 0,
                "p": 0,
                "k": 0,
            },
            "cautions": {"en": [], "fr": []},
            "instructions": {"en": [], "fr": []},
            "guaranteed_analysis": {
                "title": {"en": "string", "fr": "string"},
                "is_minimal": False,
                "en": [],
                "fr": [],
            },
        }
        self.mock_inspection = Inspection.model_validate(self.sample_inspection_dict)

        self.sample_label_data = {
            "cautions_en": ["string"],
            "instructions_en": [],
            "cautions_fr": ["string"],
            "ingredients_en": [],
            "manufacturer_address": "string",
            "instructions_fr": [],
            "manufacturer_phone_number": "string",
            "density": {"value": 0, "unit": "string"},
            "guaranteed_analysis_en": {
                "title": "string",
                "nutrients": [],
                "is_minimal": True,
            },
            "ingredients_fr": [],
            "npk": "string",
            "guaranteed_analysis_fr": {
                "title": "string",
                "nutrients": [],
                "is_minimal": True,
            },
            "company_name": "string",
            "manufacturer_website": "string",
            "registration_number": "string",
            "fertiliser_name": "string",
            "company_address": "string",
            "lot_number": "string",
            "weight": [],
            "manufacturer_name": "string",
            "company_website": "string",
            "volume": {"value": 0, "unit": "string"},
            "company_phone_number": "string",
        }
        self.label_data_json = json.dumps(self.sample_label_data)

        self.files = [
            ("files", ("image1.png", BytesIO(b"fake_image_data_1"), "image/png")),
            ("files", ("image2.png", BytesIO(b"fake_image_data_2"), "image/png")),
        ]

    @patch("app.main.read_all")
    def test_get_inspections(self, mock_read_all_inspections):
        mock_read_all_inspections.return_value = self.mock_inspection_data
        response = self.client.get("/inspections")
        self.assertEqual(response.status_code, 200)
        [InspectionData.model_validate(data) for data in response.json()]

    def test_get_inspections_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.get("/inspections")
        self.assertEqual(response.status_code, 401)

    @patch("app.main.read")
    def test_get_inspection(self, mock_read_inspection):
        mock_read_inspection.return_value = self.mock_inspection
        response = self.client.get(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 200)
        Inspection.model_validate(response.json())

    @patch("app.main.read")
    def test_get_inspection_not_found(self, mock_read_inspection):
        mock_read_inspection.side_effect = InspectionNotFoundError()
        response = self.client.get(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_get_inspection_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.get(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 401)

    @patch("app.main.create")
    def test_create_inspection(self, mock_create_inspection):
        mock_create_inspection.return_value = self.mock_inspection
        response = self.client.post(
            "/inspections",
            data={"label_data": self.label_data_json},
            files=self.files,
        )
        self.assertEqual(response.status_code, 200)
        Inspection.model_validate(response.json())

    @patch("app.main.create")
    def test_create_inspection_empty_files(self, mock_create_inspection):
        response = self.client.post("/inspections")
        self.assertEqual(response.status_code, 422)

    def test_create_inspection_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.post(
            "/inspections",
            data={"label_data": self.label_data_json},
            files=self.files,
        )
        self.assertEqual(response.status_code, 401)
