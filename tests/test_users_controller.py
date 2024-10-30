import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from datastore import UserAlreadyExistsError as DBUserAlreadyExistsError
from datastore.db.queries.user import UserNotFoundError as DBUserNotFoundError

from app.connection_manager import ConnectionManager
from app.controllers.users import sign_in, sign_up
from app.exceptions import MissingUsernameError, UserConflictError, UserNotFoundError
from app.models.users import User


class TestSignUpSuccess(unittest.IsolatedAsyncioTestCase):
    async def test_successful_user_sign_up(self):
        # Arrange
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor

        mock_user = User(username="test_user")
        mock_new_user = AsyncMock(return_value=MagicMock(id=1))
        mock_storage_url = "mocked_storage_url"

        with patch("app.controllers.users.new_user", mock_new_user), patch(
            "app.controllers.users.FERTISCAN_STORAGE_URL", mock_storage_url
        ):
            # Act
            result = await sign_up(mock_cm, mock_user)

        # Assert
        mock_cm.get_cursor.assert_called_once()
        mock_new_user.assert_awaited_once_with(
            mock_cursor, "test_user", mock_storage_url
        )
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, "test_user")

    async def test_sign_up_missing_username(self):
        # Arrange
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_user = User(username="")  # Empty username

        # Act & Assert
        with self.assertRaises(MissingUsernameError):
            await sign_up(mock_cm, mock_user)

    async def test_sign_up_user_already_exists(self):
        # Arrange
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor

        mock_user = User(username="existing_user")
        mock_new_user = AsyncMock(
            side_effect=DBUserAlreadyExistsError
        )  # Simulate user conflict

        with patch("app.controllers.users.new_user", mock_new_user):
            # Act & Assert
            with self.assertRaises(UserConflictError):
                await sign_up(mock_cm, mock_user)

    async def test_successful_user_sign_in(self):
        # Arrange
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor

        mock_user = User(username="test_user")
        mock_get_user = AsyncMock(return_value=MagicMock(id=1))

        with patch("app.controllers.users.get_user", mock_get_user):
            # Act
            result = await sign_in(mock_cm, mock_user)

        # Assert
        mock_cm.get_cursor.assert_called_once()
        mock_get_user.assert_awaited_once_with(mock_cursor, "test_user")
        self.assertEqual(result.id, 1)
        self.assertEqual(result.username, "test_user")

    async def test_sign_in_missing_username(self):
        # Arrange
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_user = User(username="")  # Empty username

        # Act & Assert
        with self.assertRaises(MissingUsernameError):
            await sign_in(mock_cm, mock_user)

    async def test_sign_in_user_not_found(self):
        # Arrange
        mock_cm = MagicMock(spec=ConnectionManager)
        mock_cursor = MagicMock()
        mock_cm.get_cursor.return_value.__enter__.return_value = mock_cursor

        mock_user = User(username="non_existent_user")
        mock_get_user = AsyncMock(
            side_effect=DBUserNotFoundError
        )  # Simulate user not found

        with patch("app.controllers.users.get_user", mock_get_user):
            # Act & Assert
            with self.assertRaises(UserNotFoundError):
                await sign_in(mock_cm, mock_user)


# Run this test case if executing as a standalone script
if __name__ == "__main__":
    unittest.main()
