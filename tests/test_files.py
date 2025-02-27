import io
import unittest
import uuid
from unittest.mock import MagicMock, patch

from datastore.blob.azure_storage_api import build_container_name
from PIL import Image
from psycopg_pool import ConnectionPool

from app.controllers.files import (
    create_folder,
    delete_folder,
    read_file,
    read_folder,
    read_folders,
)
from app.exceptions import (
    FileCreationError,
    FileNotFoundError,
    FolderCreationError,
    FolderDeletionError,
    FolderNotFoundError,
    StorageFileNotFound,
    UserNotFoundError,
)
from app.models.files import Folder


class TestReadFolders(unittest.IsolatedAsyncioTestCase):
    async def test_read_folders_success(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        sample_folders = [
            {"id": uuid.uuid4(), "owner_id": user_id, "name": "Folder1"},
            {"id": uuid.uuid4(), "owner_id": user_id, "name": "Folder2"},
        ]
        mock_cursor.fetchall.return_value = sample_folders

        folders = await read_folders(mock_cp, user_id)

        self.assertEqual(len(folders), len(sample_folders))
        for folder, sample in zip(folders, sample_folders):
            self.assertIsInstance(folder, Folder)
            self.assertEqual(folder.id, sample["id"])
            self.assertEqual(folder.owner_id, sample["owner_id"])
            self.assertEqual(folder.name, sample["name"])

    async def test_read_folders_with_string_user_id(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        sample_folders = [
            {"id": uuid.uuid4(), "owner_id": user_id, "name": "Folder1"},
            {"id": uuid.uuid4(), "owner_id": user_id, "name": "Folder2"},
        ]
        mock_cursor.fetchall.return_value = sample_folders

        folders = await read_folders(mock_cp, user_id)

        self.assertEqual(len(folders), len(sample_folders))
        for folder, sample in zip(folders, sample_folders):
            self.assertIsInstance(folder, Folder)
            self.assertEqual(folder.id, sample["id"])
            self.assertEqual(folder.owner_id, sample["owner_id"])
            self.assertEqual(folder.name, sample["name"])

    async def test_read_folders_no_results(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        mock_cursor.fetchall.return_value = []

        folders = await read_folders(mock_cp, user_id)

        self.assertEqual(folders, [])


class TestReadFolder(unittest.IsolatedAsyncioTestCase):
    async def test_read_folder_success(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        picture_set_id = uuid.uuid4()
        sample_folder = {
            "id": picture_set_id,
            "owner_id": user_id,
            "file_ids": [uuid.uuid4(), uuid.uuid4()],
        }
        mock_cursor.fetchone.return_value = sample_folder

        folder = await read_folder(mock_cp, user_id, picture_set_id)

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, picture_set_id)
        self.assertEqual(folder.owner_id, user_id)
        self.assertEqual(folder.file_ids, sample_folder["file_ids"])

    async def test_read_folder_not_found(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        picture_set_id = uuid.uuid4()
        mock_cursor.fetchone.return_value = None

        with self.assertRaises(FolderNotFoundError) as context:
            await read_folder(mock_cp, user_id, picture_set_id)

        self.assertIn(f"Folder {picture_set_id} not found", str(context.exception))


class TestDeleteFolder(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.files.StorageBackend")
    async def test_delete_folder_success(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_storage_instance = mock_storage.return_value
        mock_storage_instance.delete_folder = MagicMock()

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            {"id": str(folder_id), "owner_id": str(user_id)},  # Folder exists
        ]

        folder = await delete_folder(mock_cp, mock_storage_instance, user_id, folder_id)

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, folder_id)

        mock_storage_instance.delete_folder.assert_called_once()

    @patch("app.controllers.files.StorageBackend")
    async def test_delete_folder_user_not_found(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None  # User not found

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        with self.assertRaises(UserNotFoundError):
            await delete_folder(mock_cp, mock_storage.return_value, user_id, folder_id)

    @patch("app.controllers.files.StorageBackend")
    async def test_delete_folder_default_folder(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(folder_id)},  # User exists
        ]

        with self.assertRaises(FolderDeletionError):
            await delete_folder(mock_cp, mock_storage.return_value, user_id, folder_id)

    @patch("app.controllers.files.StorageBackend")
    async def test_delete_folder_not_found(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            None,  # Folder not found
        ]

        with self.assertRaises(FolderNotFoundError):
            await delete_folder(mock_cp, mock_storage.return_value, user_id, folder_id)

    @patch("app.controllers.files.StorageBackend")
    async def test_delete_folder_storage_error(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_storage_instance = mock_storage.return_value
        mock_storage_instance.delete_folder.side_effect = Exception("Storage error")

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            {"id": str(folder_id), "owner_id": str(user_id)},  # Folder exists
        ]

        with self.assertRaises(FolderDeletionError):
            await delete_folder(mock_cp, mock_storage_instance, user_id, folder_id)


class TestCreateFolder(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        """Generate a valid in-memory image once for all tests."""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        cls.image = img_bytes.getvalue()

    @patch("app.controllers.files.StorageBackend")
    async def test_create_folder_success(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_storage_instance = mock_storage.return_value
        mock_storage_instance.save_file = MagicMock()

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        file_id_1 = uuid.uuid4()
        file_id_2 = uuid.uuid4()
        files = [self.image, self.image]

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            {"id": str(folder_id), "owner_id": str(user_id)},  # Folder created
            {"id": str(file_id_1), "picture_set_id": str(folder_id)},  # First file
            {"id": str(file_id_2), "picture_set_id": str(folder_id)},  # Second file
        ]

        folder = await create_folder(
            mock_cp, mock_storage_instance, user_id, files, name="test_folder"
        )

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, folder_id)
        self.assertEqual(len(folder.file_ids), len(files))

        mock_storage_instance.save_file.assert_called()

    @patch("app.controllers.files.StorageBackend")
    async def test_create_folder_user_not_found(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None  # User not found

        user_id = uuid.uuid4()
        files = [self.image]

        with self.assertRaises(UserNotFoundError):
            await create_folder(mock_cp, mock_storage.return_value, user_id, files)

    @patch("app.controllers.files.StorageBackend")
    async def test_create_folder_fallback_to_default(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        files = [self.image, self.image]  # Two files
        default_folder_id = uuid.uuid4()
        file_id_1 = uuid.uuid4()
        file_id_2 = uuid.uuid4()

        mock_cursor.fetchone.side_effect = [
            {
                "id": str(user_id),
                "default_folder_id": str(default_folder_id),
            },  # Get user
            None,  # Folder creation failed
            {
                "id": str(default_folder_id),
                "owner_id": str(user_id),
            },  # Fallback to default folder
            {
                "id": str(file_id_1),
                "picture_set_id": str(default_folder_id),
            },  # Insert file 1
            {
                "id": str(file_id_2),
                "picture_set_id": str(default_folder_id),
            },  # Insert file 2
        ]

        folder = await create_folder(mock_cp, mock_storage.return_value, user_id, files)

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, default_folder_id)
        self.assertEqual(len(folder.file_ids), len(files))

    @patch("app.controllers.files.StorageBackend")
    async def test_create_folder_fails(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        files = [self.image]

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            None,  # Folder creation failed
            None,  # No default folder found
        ]

        with self.assertRaises(FolderCreationError):
            await create_folder(mock_cp, mock_storage.return_value, user_id, files)

    @patch("app.controllers.files.StorageBackend")
    async def test_create_folder_file_creation_fails(self, mock_storage):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_storage_instance = mock_storage.return_value
        mock_storage_instance.save_file = MagicMock()

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        files = [self.image]

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            {"id": str(folder_id), "owner_id": str(user_id)},  # Folder created
            None,  # File creation failed
        ]

        with self.assertRaises(FileCreationError):
            await create_folder(mock_cp, mock_storage_instance, user_id, files)


class TestReadFile(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.files.StorageBackend")
    async def test_valid_file_returns_blob(self, mock_storage):
        """Test that a valid file returns expected binary data."""
        mock_storage_instance = mock_storage.return_value
        expected_blob = b"sample binary data"
        mock_storage_instance.read_file.return_value = expected_blob

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        file_id = uuid.uuid4()

        blob = await read_file(mock_storage_instance, user_id, folder_id, file_id)

        self.assertEqual(blob, expected_blob)
        mock_storage_instance.read_file.assert_called_once_with(
            build_container_name(str(user_id)), str(folder_id), str(file_id)
        )

    @patch("app.controllers.files.StorageBackend")
    async def test_file_not_found_raises_error(self, mock_storage):
        """Test that a missing file raises FileNotFoundError."""
        mock_storage_instance = mock_storage.return_value
        mock_storage_instance.read_file.side_effect = StorageFileNotFound()

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        file_id = uuid.uuid4()

        with self.assertRaises(FileNotFoundError):
            await read_file(mock_storage_instance, user_id, folder_id, file_id)

        mock_storage_instance.read_file.assert_called_once_with(
            build_container_name(str(user_id)), str(folder_id), str(file_id)
        )
