import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from datastore import UserAlreadyExistsError as DBUserAlreadyExistsError
from datastore.db.queries.user import UserNotFoundError as DBUserNotFoundError

from app.connection_manager import ConnectionManager
from app.controllers.users import sign_in, sign_up
from app.exceptions import (
    MissingUserAttributeError,
    UserConflictError,
    UserNotFoundError,
)
from app.models.users import User


class TestSignUpSuccess(unittest.IsolatedAsyncioTestCase):
    async def test_successful_user_sign_up(self):
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor
        mock_user = User(username="test_user")
        mock_new_user = AsyncMock(return_value=MagicMock(id=1))
        mock_storage_url = "mocked_storage_url"

        with patch("app.controllers.users.new_user", mock_new_user):
            result = await sign_up(mock_cm, mock_user, mock_storage_url)

        mock_cm.get_cursor.assert_called_once()
        mock_new_user.assert_awaited_once_with(
            mock_cursor, "test_user", mock_storage_url
        )
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, "test_user")

    async def test_sign_up_missing_username(self):
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_user = User(username="")

        with self.assertRaises(MissingUserAttributeError):
            await sign_up(mock_cm, mock_user, "mock_storage_url")

    async def test_sign_up_user_already_exists(self):
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor
        mock_user = User(username="existing_user")
        mock_new_user = AsyncMock(side_effect=DBUserAlreadyExistsError)

        with patch("app.controllers.users.new_user", mock_new_user):
            with self.assertRaises(UserConflictError):
                await sign_up(mock_cm, mock_user, "mock_storage_url")

    async def test_successful_user_sign_in(self):
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor
        mock_user = User(username="test_user")
        mock_get_user = AsyncMock(return_value=MagicMock(id=1))

        with patch("app.controllers.users.get_user", mock_get_user):
            result = await sign_in(mock_cm, mock_user)

        mock_cm.get_cursor.assert_called_once()
        mock_get_user.assert_awaited_once_with(mock_cursor, "test_user")
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, "test_user")

    async def test_sign_in_missing_username(self):
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_user = User(username="")

        with self.assertRaises(MissingUserAttributeError):
            await sign_in(mock_cm, mock_user)

    async def test_sign_in_user_not_found(self):
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor
        mock_user = User(username="non_existent_user")
        mock_get_user = AsyncMock(side_effect=DBUserNotFoundError)

        with patch("app.controllers.users.get_user", mock_get_user):
            with self.assertRaises(UserNotFoundError):
                await sign_in(mock_cm, mock_user)
