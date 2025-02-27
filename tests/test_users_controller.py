import unittest
from unittest.mock import MagicMock
from uuid import uuid4

from app.controllers.users import sign_in, sign_up
from app.exceptions import (
    MissingUserAttributeError,
    UserConflictError,
    UserNotFoundError,
)
from app.models.users import User


class TestSignUpSuccess(unittest.IsolatedAsyncioTestCase):
    async def test_successful_user_sign_up(self):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        mock_user = User(username="test_user")
        user_id = uuid4()
        mock_new_user = {"id": user_id, "email": "test_user"}

        cursor_mock.fetchone.return_value = mock_new_user

        result = await sign_up(cp, mock_user)

        cp.connection.assert_called_once()
        cursor_mock.execute.assert_called_once()
        self.assertEqual(result.id, user_id)  # Ensure UUID matches
        self.assertEqual(result.username, "test_user")

    async def test_sign_up_missing_username(self):
        cp = MagicMock()
        mock_user = User(username="")

        with self.assertRaises(MissingUserAttributeError):
            await sign_up(cp, mock_user)

    async def test_sign_up_user_already_exists(self):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        mock_user = User(username="existing_user")

        cursor_mock.fetchone.return_value = None  # Simulating conflict

        with self.assertRaises(UserConflictError):
            await sign_up(cp, mock_user)

    async def test_successful_user_sign_in(self):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        mock_user = User(username="test_user")
        mock_existing_user = {"id": uuid4(), "email": "test_user"}
        cursor_mock.fetchone.return_value = mock_existing_user

        result = await sign_in(cp, mock_user)

        cp.connection.assert_called_once()
        cursor_mock.execute.assert_called_once()
        self.assertEqual(result.id, mock_existing_user["id"])
        self.assertEqual(result.username, "test_user")

    async def test_sign_in_missing_username(self):
        cp = MagicMock()
        mock_user = User(username="")

        with self.assertRaises(MissingUserAttributeError):
            await sign_in(cp, mock_user)

    async def test_sign_in_user_not_found(self):
        cp = MagicMock()
        conn_mock = MagicMock()
        cursor_mock = MagicMock()
        conn_mock.cursor.return_value.__enter__.return_value = cursor_mock
        cp.connection.return_value.__enter__.return_value = conn_mock
        mock_user = User(username="non_existent_user")

        cursor_mock.fetchone.return_value = None  # Simulating user not found

        with self.assertRaises(UserNotFoundError):
            await sign_in(cp, mock_user)
