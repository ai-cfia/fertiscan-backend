import unittest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.connection_manager import ConnectionManager
from app.controllers.inspections import read_all
from app.exceptions import MissingUserAttributeError
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
        cm.get_cursor.return_value.__enter__.return_value = MagicMock()
        user = User(id=uuid.uuid4())

        # Execute the function
        inspections = await read_all(cm, user)

        # Check that get_user_analysis_by_verified was called twice
        self.assertEqual(mock_get_user_analysis_by_verified.call_count, 2)
        mock_get_user_analysis_by_verified.assert_any_call(
            cm.get_cursor.return_value.__enter__.return_value, user.id, True
        )
        mock_get_user_analysis_by_verified.assert_any_call(
            cm.get_cursor.return_value.__enter__.return_value, user.id, False
        )

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
        cm.get_cursor.return_value.__enter__.return_value = MagicMock()
        user = User(id=uuid.uuid4())

        # Execute the function
        inspections = await read_all(cm, user)

        # Verify that an empty list is returned when there are no inspections
        self.assertEqual(len(inspections), 0)
