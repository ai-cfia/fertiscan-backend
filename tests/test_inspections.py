import json
import unittest
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

from datastore.blob.azure_storage_api import build_container_name
from fertiscan.db.queries.inspection import (
    InspectionNotFoundError as DBInspectionNotFoundError,
)

from app.controllers.inspections import (
    get_pictures,
    create_inspection,
    delete_inspection,
    read_all_inspections,
    read_inspection,
    update_inspection,
)
from app.exceptions import InspectionNotFoundError, MissingUserAttributeError
from app.models.inspections import (
    DeletedInspection,
    InspectionResponse,
    InspectionUpdate,
)
from app.models.label_data import LabelData
from app.models.users import User


class TestReadAll(unittest.IsolatedAsyncioTestCase):
    async def test_missing_user_id_raises_error(self):
        cp = MagicMock()
        user = User(id=None)

        with self.assertRaises(MissingUserAttributeError):
            await read_all_inspections(cp, user)

    @patch("app.controllers.inspections.get_user_analysis_by_verified")
    async def test_calls_analysis_twice_and_combines_results(
        self, mock_get_user_analysis_by_verified
    ):
        mock_get_user_analysis_by_verified.side_effect = [
            [
                (
                    uuid.uuid4(),
                    datetime(2023, 1, 1),
                    datetime(2023, 1, 2),
                    uuid.uuid4(),
                    uuid.uuid4(),
                    uuid.uuid4(),
                    "Product A",
                    uuid.uuid4(),
                    "Company A",
                    True,
                )
            ],
            [
                (
                    uuid.uuid4(),
                    datetime(2023, 1, 3),
                    datetime(2023, 1, 4),
                    uuid.uuid4(),
                    uuid.uuid4(),
                    uuid.uuid4(),
                    "Product B",
                    uuid.uuid4(),
                    "Company B",
                    False,
                )
            ],
        ]

        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        user = User(id=uuid.uuid4())

        inspections = await read_all_inspections(cp, user)

        self.assertEqual(mock_get_user_analysis_by_verified.call_count, 2)
        mock_get_user_analysis_by_verified.assert_any_call(cursor_mock, user.id, True)
        mock_get_user_analysis_by_verified.assert_any_call(cursor_mock, user.id, False)

        self.assertEqual(len(inspections), 2)
        self.assertEqual(inspections[0].product_name, "Product A")
        self.assertEqual(inspections[1].product_name, "Product B")

    @patch("app.controllers.inspections.get_user_analysis_by_verified")
    async def test_no_inspections_for_verified_and_unverified(
        self, mock_get_user_analysis_by_verified
    ):
        mock_get_user_analysis_by_verified.side_effect = [[], []]

        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        user = User(id=uuid.uuid4())

        inspections = await read_all_inspections(cp, user)
        self.assertEqual(len(inspections), 0)


class TestRead(unittest.IsolatedAsyncioTestCase):
    async def test_missing_user_id_raises_error(self):
        cp = MagicMock()
        user = User(id=None)
        inspection_id = uuid.uuid4()

        with self.assertRaises(MissingUserAttributeError):
            await read_inspection(cp, user, inspection_id)

    async def test_missing_inspection_id_raises_error(self):
        cp = MagicMock()
        user = User(id=uuid.uuid4())

        with self.assertRaises(ValueError):
            await read_inspection(cp, user, None)

    async def test_invalid_inspection_id_format(self):
        cp = MagicMock()
        user = User(id=uuid.uuid4())
        invalid_id = "not-a-uuid"

        with self.assertRaises(ValueError):
            await read_inspection(cp, user, invalid_id)

    @patch("app.controllers.inspections.get_inspection_dict")
    async def test_valid_inspection_id_calls_get_full_inspection_json(
        self, mock_get_inspection_dict
    ):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock

        user = User(id=uuid.uuid4())
        inspection_id = uuid.uuid4()

        sample_inspection = {
            "inspection_id": str(inspection_id),
            "inspection_comment": "string",
            "verified": False,
            "organizations": [],
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

        mock_get_inspection_dict.return_value = json.dumps(sample_inspection)

        inspection = await read_inspection(cp, user, inspection_id)

        mock_get_inspection_dict.assert_called_once_with(
            cursor_mock,
            inspection_id,
        )
        self.assertIsInstance(inspection, InspectionResponse)

    @patch("app.controllers.inspections.get_inspection_controller")
    @patch("app.controllers.inspections.ContainerController.get_folder_pictures")
    async def test_get_pictures_success(self, mock_get_folder_pictures, mock_get_inspection_controller):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        controller_mock = MagicMock()

        user = User(id=uuid.uuid4())
        inspection_id = uuid.uuid4()
        container_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        mock_get_inspection_controller.return_value = controller_mock
        controller_mock.get_inspection_image_location_data.return_value = (container_id, folder_id)
        mock_get_folder_pictures.return_value = ["picture1.jpg", "picture2.jpg"]


        pictures = await get_pictures(cp, user, inspection_id)

        mock_get_inspection_controller.assert_called_once_with(cursor_mock, inspection_id)
        controller_mock.get_inspection_image_location_data.assert_called_once_with(cursor_mock)
        mock_get_folder_pictures.assert_called_once_with(cursor_mock, folder_id, user.id)

        self.assertIsInstance(pictures, list)
        self.assertEqual(pictures, ["picture1.jpg", "picture2.jpg"])

    @patch("app.controllers.inspections.get_inspection_dict")
    async def test_inspection_not_found_raises_error(
        self, mock_get_full_inspection_analysis
    ):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock

        user = User(id=uuid.uuid4())
        inspection_id = uuid.uuid4()

        mock_get_full_inspection_analysis.side_effect = DBInspectionNotFoundError(
            "Not found"
        )

        with self.assertRaises(InspectionNotFoundError):
            await read_inspection(cp, user, inspection_id)


class TestCreateFunction(unittest.IsolatedAsyncioTestCase):
    async def test_missing_user_id_raises_error(self):
        cp = MagicMock()
        label_data = LabelData()
        label_images = [b"image_data"]
        user = User(id=None)

        with self.assertRaises(MissingUserAttributeError):
            await create_inspection(cp, user, label_data, label_images)

    @patch("app.controllers.inspections.new_inspection")
    async def test_create_inspection_success(
        self, mock_new_inspection
    ):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        user = User(id=uuid.uuid4())
        label_data = LabelData()
        label_images = [b"image_data"]
        inspection_id = uuid.uuid4()
        mock_inspection_data = {
            "inspection_id": inspection_id,
            "inspection_comment": "string",
            "verified": False,
            "company": {},
            "manufacturer": {},
            "product": {
                "name": "Sample Product",
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
            "folder_id": str(uuid.uuid4()),
            "container_id": str(uuid.uuid4()),
        }
        mock_new_inspection.return_value = mock_inspection_data

        inspection = await create_inspection(
            cp, user, label_data, label_images
        )

        mock_new_inspection.assert_called_once_with(
            cursor_mock,
            user.id,
            label_data.model_dump(),
        )
        self.assertIsInstance(inspection, InspectionResponse)
        self.assertEqual(inspection.inspection_id, inspection_id)

    async def test_missing_label_data_raises_error(self):
        cp = MagicMock()
        label_images = [b"image_data"]
        user = User(id=uuid.uuid4())

        with self.assertRaises(ValueError):
            await create_inspection(cp, user, None, label_images)


class TestUpdateFunction(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.cp = MagicMock()
        self.user = User(id=uuid.uuid4())
        self.inspection_id = uuid.uuid4()

        # Valid update data in dictionary form
        self.update_data = {
            "inspection_comment": "string",
            "verified": False,
            "company": {},
            "manufacturer": {},
            "product": {
                "name": "string",
                "label_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "registration_numbers": [
                    {
                        "registration_number": "3066014L",
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
            "folder_id": str(uuid.uuid4()),
            "container_id": str(uuid.uuid4()),
        }

        # Convert dict to InspectionUpdate model for tests that require validation
        self.inspection_update = InspectionUpdate.model_validate(self.update_data)

    async def test_missing_user_id_raises_error(self):
        self.user.id = None
        with self.assertRaises(MissingUserAttributeError):
            await update_inspection(
                self.cp, self.user, self.inspection_id, self.inspection_update
            )

    async def test_missing_inspection_id_raises_error(self):
        with self.assertRaises(ValueError):
            await update_inspection(self.cp, self.user, None, self.inspection_update)

    async def test_missing_inspection_update_data_raises_error(self):
        with self.assertRaises(ValueError):
            await update_inspection(self.cp, self.user, self.inspection_id, None)

    async def test_invalid_inspection_id_format(self):
        invalid_id = "not-a-uuid"
        with self.assertRaises(ValueError):
            await update_inspection(
                self.cp, self.user, invalid_id, self.inspection_update
            )

class TestDeleteFunction(unittest.IsolatedAsyncioTestCase):
    async def test_missing_user_id_raises_error(self):
        cp = MagicMock()
        user = User(id=None)
        inspection_id = uuid.uuid4()

        with self.assertRaises(MissingUserAttributeError):
            await delete_inspection(cp, user, inspection_id)

    async def test_missing_inspection_id_raises_error(self):
        cp = MagicMock()
        user = User(id=uuid.uuid4())

        with self.assertRaises(ValueError):
            await delete_inspection(cp, user, None)

    async def test_invalid_inspection_id_format(self):
        cp = MagicMock()
        user = User(id=uuid.uuid4())
        invalid_id = "not-a-uuid"

        with self.assertRaises(ValueError):
            await delete_inspection(cp, user, invalid_id)

    @patch("app.controllers.inspections.get_inspection_controller")
    async def test_delete_inspection_success(self, mock_get_inspection_controller):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        controller_mock = MagicMock()

        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        mock_get_inspection_controller.return_value = controller_mock
        mock_delete_inspection = controller_mock.delete_inspection

        user = User(id=uuid.uuid4())
        inspection_id = uuid.uuid4()

        mock_deleted_inspection_data = {
            "id": inspection_id,
            "deleted": True,
        }
        mock_delete_inspection.return_value = DeletedInspection(**mock_deleted_inspection_data)

        deleted_inspection = await delete_inspection(cp, user, inspection_id)

        mock_get_inspection_controller.assert_called_once_with(cursor_mock, inspection_id)
        mock_delete_inspection.assert_called_once_with(cursor_mock, user.id)

        self.assertIsInstance(deleted_inspection, DeletedInspection)
        self.assertEqual(deleted_inspection.id, inspection_id)
        self.assertTrue(deleted_inspection.deleted)