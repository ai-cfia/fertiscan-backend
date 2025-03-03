import base64
import unittest
import uuid
from datetime import datetime
from unittest.mock import ANY, Mock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pipeline import FertilizerInspection

from app.dependencies import (
    authenticate_user,
    fetch_user,
    get_connection_pool,
    get_gpt,
    get_ocr,
    get_settings,
    get_storage,
)
from app.exceptions import (
    FileNotFoundError,
    FolderNotFoundError,
    InspectionNotFoundError,
    UserConflictError,
)
from app.models.files import DeleteFolderResponse, Folder
from app.models.inspections import DeletedInspection, InspectionData, InspectionResponse
from app.models.label_data import LabelData
from app.models.users import User
from tests import app


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

        def override_mock():
            return Mock()

        app.dependency_overrides.clear()
        app.dependency_overrides[get_connection_pool] = override_mock
        app.dependency_overrides[get_ocr] = override_mock
        app.dependency_overrides[get_gpt] = override_mock
        app.dependency_overrides[fetch_user] = lambda: Mock(id="test-user")

    @patch("app.routes.extract_data")
    def test_analyze_document(self, mock_extract_data):
        mock_inspection_data = {
            "company_name": "Test Company",
            "fertiliser_name": "Mock Fertilizer",
            "registration_number": [
                {"identifier": "REG123", "type": "fertilizer_product"},
            ],
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
            validated_inspection.fertiliser_name, mock_inspection.fertiliser_name
        )
        self.assertListEqual(
            [r.model_dump() for r in validated_inspection.registration_number],
            [r.model_dump() for r in mock_inspection.registration_number],
        )

    @patch("app.routes.extract_data")
    def test_analyze_empty_file(self, mock_extract_data):
        """Test analyze_document with an empty file that triggers validation error"""
        mock_extract_data.return_value = None
        files = [("files", ("empty.txt", b"", "text/plain"))]
        response = self.client.post("/analyze", files=files)
        self.assertEqual(response.status_code, 422)

    @patch("app.routes.extract_data")
    def test_analyze_file_list_with_empty_files(self, mock_extract_data):
        """Test analyze_document with a file list containing empty files"""
        mock_inspection_data = {
            "company_name": "Test Company",
            "fertiliser_name": "Mock Fertilizer",
            "registration_number": [
                {"identifier": "REG123", "type": "fertilizer_product"},
            ],
        }
        mock_inspection = FertilizerInspection.model_validate(mock_inspection_data)
        mock_extract_data.return_value = mock_inspection
        files = [
            ("files", ("file1.txt", b"Sample content", "text/plain")),
            ("files", ("empty.txt", b"", "text/plain")),
        ]
        response = self.client.post("/analyze", files=files)
        self.assertEqual(response.status_code, 422)

    @patch("app.routes.extract_data")
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
        app.dependency_overrides[get_connection_pool] = override_dep
        app.dependency_overrides[authenticate_user] = override_dep
        app.dependency_overrides[get_settings] = override_dep
        app.dependency_overrides[fetch_user] = lambda: self.test_user

    @patch("app.routes.sign_up")
    def test_signup(self, mock_sign_up):
        mock_sign_up.return_value = self.test_user
        response = self.client.post("/signup", json={"username": "test_user"})
        self.assertEqual(response.status_code, 201)
        User.model_validate(response.json())

    @patch("app.routes.sign_up")
    def test_signup_existing_user(self, mock_sign_up):
        mock_sign_up.side_effect = UserConflictError()
        response = self.client.post("/signup", json={"username": "test_user"})
        self.assertEqual(response.status_code, 409)

    @patch("app.routes.sign_up")
    def test_signup_bad_authentication(self, _):
        del app.dependency_overrides[authenticate_user]
        response = self.client.post("/signup")
        self.assertEqual(response.status_code, 401)
        empty_username = ""
        response = self.client.post(
            "/signup",
            headers={
                "Authorization": f'Basic {self.credentials(empty_username, "password")}',
            },
        )
        self.assertEqual(response.status_code, 400)

    @patch("app.routes.sign_up")
    def test_signup_authentication_success(self, mock_sign_up):
        del app.dependency_overrides[authenticate_user]
        mock_sign_up.return_value = self.test_user
        response = self.client.post(
            "/signup",
            headers={
                "Authorization": f'Basic {self.credentials("test_user", "password")}',
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_sign_in(self):
        response = self.client.post("/login")
        self.assertEqual(response.status_code, 200)
        user = User.model_validate(response.json())
        self.assertEqual(user, self.test_user)

    def test_sign_in_user_not_found(self):
        # Simulate user not found by overriding fetch_user to raise HTTPException
        app.dependency_overrides[fetch_user] = lambda: (_ for _ in ()).throw(
            HTTPException(status_code=401, detail="User not found")
        )
        response = self.client.post("/login")
        self.assertEqual(response.status_code, 401)

    def test_sign_in_bad_authentication(self):
        del app.dependency_overrides[authenticate_user]
        del app.dependency_overrides[fetch_user]
        response = self.client.post("/login")
        self.assertEqual(response.status_code, 401)
        empty_username = ""
        response = self.client.post(
            "/login",
            headers={
                "Authorization": f"Basic {self.credentials(empty_username, 'password')}",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_sign_in_authentication_success(self):
        del app.dependency_overrides[authenticate_user]
        del app.dependency_overrides[fetch_user]
        app.dependency_overrides[fetch_user] = lambda: self.test_user
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

        self.test_user = User(username="test_user", id=uuid.uuid4())

        app.dependency_overrides.clear()
        app.dependency_overrides[get_connection_pool] = lambda: Mock()
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
                main_organization_id=uuid.uuid4(),
                main_organization_name="Company A",
                verified=True,
            ),
            InspectionData(
                id=uuid.uuid4(),
                upload_date=datetime(2023, 1, 3),
                updated_at=datetime(2023, 1, 4),
                sample_id=uuid.uuid4(),
                picture_set_id=uuid.uuid4(),
                label_info_id=uuid.uuid4(),
                product_name="Product B",
                main_organization_id=uuid.uuid4(),
                main_organization_name="Company B",
                verified=False,
            ),
        ]

        inspection_id = uuid.uuid4()
        self.sample_inspection_dict = {
            "inspection_id": str(inspection_id),
            "inspection_comment": "string",
            "verified": False,
            "product": {
                "name": "string",
                "label_id": str(uuid.uuid4()),
                "registration_numbers": [
                    {
                        "registration_number": "2224256A",
                        "is_an_ingredient": False,
                    }
                ],
                "lot_number": "string",
                "metrics": {
                    "weight": [],
                    "volume": {"edited": False},
                    "density": {"edited": False},
                },
                "npk": "10-10-10",
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
            "ingredients": {"en": [], "fr": []},
            "picture_set_id": str(uuid.uuid4()),
        }
        self.mock_inspection = InspectionResponse.model_validate(
            self.sample_inspection_dict
        )

    @patch("app.routes.read_all_inspections")
    def test_get_inspections(self, mock_read_all_inspections):
        mock_read_all_inspections.return_value = self.mock_inspection_data
        response = self.client.get("/inspections")
        self.assertEqual(response.status_code, 200)
        [InspectionData.model_validate(data) for data in response.json()]

    def test_get_inspections_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.get("/inspections")
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.read_inspection")
    def test_get_inspection(self, mock_read_inspection):
        mock_read_inspection.return_value = self.mock_inspection
        response = self.client.get(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 200)
        InspectionResponse.model_validate(response.json())

    @patch("app.routes.read_inspection")
    def test_get_inspection_not_found(self, mock_read_inspection):
        mock_read_inspection.side_effect = InspectionNotFoundError()
        response = self.client.get(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_get_inspection_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.get(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.create_inspection")
    def test_create_inspection(self, mock_create_inspection):
        mock_create_inspection.return_value = self.mock_inspection
        response = self.client.post(
            "/inspections",
            json=self.sample_inspection_dict,
        )
        self.assertEqual(response.status_code, 200, response.json())
        InspectionResponse.model_validate(response.json())

    def test_create_inspection_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.post(
            "/inspections",
            json=self.sample_inspection_dict,
        )
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.delete_inspection")
    def test_delete_inspection(self, mock_delete_inspection):
        mock_deleted_inspection = DeletedInspection(id=uuid.uuid4())
        mock_delete_inspection.return_value = mock_deleted_inspection
        response = self.client.delete(f"/inspections/{mock_deleted_inspection.id}")
        self.assertEqual(response.status_code, 200)
        DeletedInspection.model_validate(response.json())

    @patch("app.routes.delete_inspection")
    def test_delete_inspection_not_found(self, mock_delete_inspection):
        mock_delete_inspection.side_effect = InspectionNotFoundError()
        response = self.client.delete(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)

    def test_delete_inspection_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.delete(f"/inspections/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.update_inspection")
    def test_update_inspection(self, mock_update_inspection):
        return_data = self.sample_inspection_dict.copy()
        return_data["inspection_id"] = uuid.uuid4()
        return_inspection = InspectionResponse.model_validate(return_data)
        mock_update_inspection.return_value = return_inspection
        inspection_id = uuid.uuid4()

        response = self.client.put(
            f"/inspections/{inspection_id}", json=self.sample_inspection_dict
        )
        self.assertEqual(response.status_code, 200)

        inspection_response = InspectionResponse.model_validate(response.json())
        self.assertEqual(inspection_response.inspection_comment, "string")
        self.assertEqual(inspection_response.verified, False)
        self.assertEqual(
            inspection_response.product.registration_numbers[0].registration_number,
            "2224256A",
        )

    @patch("app.routes.update_inspection")
    def test_update_inspection_not_found(self, mock_update_inspection):
        mock_update_inspection.side_effect = InspectionNotFoundError()
        inspection_id = uuid.uuid4()

        response = self.client.put(
            f"/inspections/{inspection_id}", json=self.sample_inspection_dict
        )
        self.assertEqual(response.status_code, 404)

    def test_update_inspection_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        inspection_id = uuid.uuid4()

        response = self.client.put(
            f"/inspections/{inspection_id}", json=self.sample_inspection_dict
        )
        self.assertEqual(response.status_code, 401)

    def test_update_inspection_invalid_data(self):
        inspection_id = uuid.uuid4()

        response = self.client.put(
            f"/inspections/{inspection_id}", json={"verified": True}
        )
        self.assertEqual(response.status_code, 422)


class TestAPIFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        self.test_user = User(username="test_user", id=uuid.uuid4())

        app.dependency_overrides.clear()
        app.dependency_overrides[get_connection_pool] = lambda: Mock()
        app.dependency_overrides[fetch_user] = lambda: self.test_user
        app.dependency_overrides[get_settings] = lambda: Mock(
            azure_storage_connection_string="mock_connection_string"
        )
        self.mock_get_storage = Mock()
        app.dependency_overrides[get_storage] = lambda: self.mock_get_storage

        self.folder_id = uuid.uuid4()
        self.file_id = uuid.uuid4()

    @patch("app.routes.read_inspection_folders")
    def test_get_folders_success(self, mock_read_folders):
        folder_1 = Folder(
            id=uuid.uuid4(), owner_id=self.test_user.id, file_ids=[uuid.uuid4()]
        )
        folder_2 = Folder(
            id=uuid.uuid4(),
            owner_id=self.test_user.id,
            file_ids=[uuid.uuid4(), uuid.uuid4()],
        )
        mock_read_folders.return_value = [folder_1, folder_2]

        response = self.client.get("/files")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(set(data[0]["file_ids"]), {str(folder_1.file_ids[0])})
        self.assertEqual(
            set(data[1]["file_ids"]),
            {str(folder_2.file_ids[0]), str(folder_2.file_ids[1])},
        )

    def test_get_folders_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.get("/files")
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.read_inspection_folder")
    def test_get_folder(self, mock_read_folder):
        folder_id = self.folder_id
        file_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_read_folder.return_value = Folder(
            id=folder_id, owner_id=self.test_user.id, file_ids=file_ids
        )
        response = self.client.get(f"/files/{folder_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], str(folder_id))
        self.assertEqual(set(data["file_ids"]), {str(file_ids[0]), str(file_ids[1])})

    def test_get_folder_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.get(f"/files/{self.folder_id}")
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.read_inspection_folder")
    def test_get_folder_not_found(self, mock_read_folder):
        mock_read_folder.side_effect = FolderNotFoundError()
        response = self.client.get(f"/files/{self.folder_id}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Folder not found")

    @patch("app.routes.create_inspection_folder")
    def test_post_files_success(self, mock_create_folder):
        folder_id = uuid.uuid4()
        file_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_create_folder.return_value = Folder(id=folder_id, file_ids=file_ids)
        files = [
            ("files", ("test1.png", b"fake_image_data1", "image/png")),
            ("files", ("test2.png", b"fake_image_data2", "image/png")),
        ]
        response = self.client.post("/files", files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], str(folder_id))
        self.assertEqual(set(data["file_ids"]), {str(file_ids[0]), str(file_ids[1])})
        mock_create_folder.assert_called_once()

    def test_post_files_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.post("/files", files=[])
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.create_inspection_folder")
    def test_post_files_empty(self, mock_create_folder):
        response = self.client.post("/files", files=[])
        self.assertEqual(response.status_code, 422)
        mock_create_folder.assert_not_called()

    @patch("app.routes.delete_inspection_folder")
    def test_delete_folder_success(self, mock_delete_folder):
        mock_delete_folder.return_value = DeleteFolderResponse(
            id=self.folder_id, deleted=True
        )

        response = self.client.delete(f"/files/{self.folder_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], str(self.folder_id))
        self.assertTrue(data["deleted"])
        mock_delete_folder.assert_called_once_with(
            ANY, self.mock_get_storage, self.test_user.id, self.folder_id
        )

    def test_delete_folder_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.delete(f"/files/{self.folder_id}")
        self.assertEqual(response.status_code, 401)

    @patch("app.routes.delete_inspection_folder")
    def test_delete_folder_not_found(self, mock_delete_folder):
        mock_delete_folder.side_effect = FolderNotFoundError()
        response = self.client.delete(f"/files/{self.folder_id}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Folder not found")

    @patch("app.routes.read_label")
    async def test_get_file(self, mock_read_label):
        mock_read_label.return_value = b"fake_image_data"
        response = self.client.get(f"/files/{self.folder_id}/{self.file_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"fake_image_data")
        self.assertEqual(response.headers["content-type"], "image/png")
        mock_read_label.assert_called_once_with(
            ANY, self.test_user.id, self.folder_id, self.file_id
        )

    @patch("app.routes.read_label")
    def test_get_file_not_found(self, mock_read_label):
        mock_read_label.side_effect = FileNotFoundError()
        response = self.client.get(f"/files/{self.folder_id}/{self.file_id}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "File not found")

    def test_get_file_unauthenticated(self):
        del app.dependency_overrides[fetch_user]
        response = self.client.get(f"/files/{self.folder_id}/{self.file_id}")
        self.assertEqual(response.status_code, 401)
