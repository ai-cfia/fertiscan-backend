import json
import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fertiscan.db.queries.inspection import (
    InspectionNotFoundError as DBInspectionNotFoundError,
)

from app.connection_manager import ConnectionManager
from app.controllers.inspections import create, read, read_all
from app.exceptions import InspectionNotFoundError, MissingUserAttributeError
from app.models.inspections import Inspection
from app.models.label_data import LabelData
from app.models.users import User


class TestReadAll(unittest.IsolatedAsyncioTestCase):
    async def test_missing_user_id_raises_error(self):
        cm = AsyncMock(spec=ConnectionManager)
        user = User(id=None)

        with self.assertRaises(MissingUserAttributeError):
            await read_all(cm, user)

    @patch("app.controllers.inspections.get_user_analysis_by_verified")
    async def test_calls_analysis_twice_and_combines_results(
        self, mock_get_user_analysis_by_verified
    ):
        # Set up mock return values for verified and unverified data
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
                    uuid.uuid4(),
                    "Company A",
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
                    uuid.uuid4(),
                    "Company B",
                )
            ],
        ]

        cm = AsyncMock(spec=ConnectionManager)
        cursor_mock = MagicMock()
        cm.get_cursor.return_value.__enter__.return_value = cursor_mock
        user = User(id=uuid.uuid4())

        # Execute the function
        inspections = await read_all(cm, user)

        # Check that get_user_analysis_by_verified was called twice
        self.assertEqual(mock_get_user_analysis_by_verified.call_count, 2)
        mock_get_user_analysis_by_verified.assert_any_call(cursor_mock, user.id, True)
        mock_get_user_analysis_by_verified.assert_any_call(cursor_mock, user.id, False)

        # Verify that the result is a list of InspectionData objects with correct length and data
        self.assertEqual(len(inspections), 2)
        self.assertEqual(inspections[0].product_name, "Product A")
        self.assertEqual(inspections[1].product_name, "Product B")

    @patch("app.controllers.inspections.get_user_analysis_by_verified")
    async def test_no_inspections_for_verified_and_unverified(
        self, mock_get_user_analysis_by_verified
    ):
        # Mock empty results for both verified and unverified inspections
        mock_get_user_analysis_by_verified.side_effect = [[], []]

        cm = AsyncMock(spec=ConnectionManager)
        cursor_mock = MagicMock()
        cm.get_cursor.return_value.__enter__.return_value = cursor_mock
        user = User(id=uuid.uuid4())

        # Execute the function
        inspections = await read_all(cm, user)

        # Verify that an empty list is returned when there are no inspections
        self.assertEqual(len(inspections), 0)


class TestRead(unittest.IsolatedAsyncioTestCase):
    async def test_missing_user_id_raises_error(self):
        cm = AsyncMock(spec=ConnectionManager)
        user = User(id=None)
        inspection_id = uuid.uuid4()

        with self.assertRaises(MissingUserAttributeError):
            await read(cm, user, inspection_id)

    async def test_missing_inspection_id_raises_error(self):
        cm = AsyncMock(spec=ConnectionManager)
        user = User(id=uuid.uuid4())

        with self.assertRaises(ValueError):
            await read(cm, user, None)

    @patch("app.controllers.inspections.get_full_inspection_json")
    async def test_invalid_inspection_id_format(self, mock_get_full_inspection_json):
        cm = AsyncMock(spec=ConnectionManager)
        user = User(id=uuid.uuid4())
        invalid_id = "not-a-uuid"

        with self.assertRaises(ValueError):
            await read(cm, user, invalid_id)

    @patch("app.controllers.inspections.get_full_inspection_json")
    async def test_valid_inspection_id_calls_get_full_inspection_json(
        self, mock_get_full_inspection_json
    ):
        cm = AsyncMock(spec=ConnectionManager)
        cursor_mock = MagicMock()
        cm.get_cursor.return_value.__enter__.return_value = cursor_mock

        user = User(id=uuid.uuid4())
        inspection_id = uuid.uuid4()

        sample_inspection = {
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

        mock_get_full_inspection_json.return_value = json.dumps(sample_inspection)

        # Execute the function
        inspection = await read(cm, user, inspection_id)

        # Verify that get_full_inspection_json was called with the correct arguments
        mock_get_full_inspection_json.assert_called_once_with(
            cursor_mock, inspection_id, user.id
        )

        # Check that the result is an Inspection object
        self.assertIsInstance(inspection, Inspection)

    @patch("app.controllers.inspections.get_full_inspection_json")
    async def test_inspection_not_found_raises_error(
        self, mock_get_full_inspection_json
    ):
        cm = AsyncMock(spec=ConnectionManager)
        cursor_mock = MagicMock()
        cm.get_cursor.return_value.__enter__.return_value = cursor_mock

        user = User(id=uuid.uuid4())
        inspection_id = uuid.uuid4()

        # Set up the mock to raise the InspectionNotFoundError
        mock_get_full_inspection_json.side_effect = DBInspectionNotFoundError(
            "Not found"
        )

        with self.assertRaises(InspectionNotFoundError):
            await read(cm, user, inspection_id)


class TestCreateFunction(unittest.IsolatedAsyncioTestCase):
    async def test_missing_user_id_raises_error(self):
        cm = AsyncMock(spec=ConnectionManager)
        label_data = LabelData()
        label_images = [b"image_data"]
        user = User(id=None)

        with self.assertRaises(MissingUserAttributeError):
            await create(cm, user, label_data, label_images, "fake_conn_str")

    @patch("app.controllers.inspections.register_analysis")
    @patch("app.controllers.inspections.ContainerClient")
    async def test_create_inspection_success(
        self, mock_container_client, mock_register_analysis
    ):
        cm = AsyncMock(spec=ConnectionManager)
        cursor_mock = MagicMock()
        cm.get_cursor.return_value.__enter__.return_value = cursor_mock
        user = User(id=uuid.uuid4())
        label_data = LabelData()
        label_images = [b"image_data"]
        inspection_id = uuid.uuid4()
        fake_conn_str = "fake_conn_str"
        mock_inspection_data = {
            "inspection_id": inspection_id,
            "inspection_comment": "string",
            "verified": False,
            "company": {},
            "manufacturer": {},
            "product": {
                "name": "Sample Product",
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
        mock_register_analysis.return_value = mock_inspection_data

        # Instantiate the mock container client
        container_client_instance = (
            mock_container_client.from_connection_string.return_value
        )

        # Call create function
        inspection = await create(cm, user, label_data, label_images, fake_conn_str)

        # Assertions
        mock_container_client.from_connection_string.assert_called_once_with(
            fake_conn_str, container_name=f"user-{user.id}"
        )
        mock_register_analysis.assert_called_once_with(
            cursor_mock,
            container_client_instance,
            user.id,
            label_images,
            label_data.model_dump(),
        )
        self.assertIsInstance(inspection, Inspection)
        self.assertEqual(inspection.inspection_id, inspection_id)
