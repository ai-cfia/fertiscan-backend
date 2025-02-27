import io
import unittest
import uuid
from unittest.mock import MagicMock

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
    FolderReadError,
    StorageFileNotFound,
    UserNotFoundError,
)
from app.models.files import Folder
from app.services.file_storage import StorageManager


class TestReadFolders(unittest.IsolatedAsyncioTestCase):
    async def test_read_folders_success(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        sample_folders = [
            {
                "id": uuid.uuid4(),
                "owner_id": user_id,
                "name": "Folder1",
                "file_ids": [uuid.uuid4()],
            },
            {
                "id": uuid.uuid4(),
                "owner_id": user_id,
                "name": "Folder2",
                "file_ids": [uuid.uuid4()],
            },
        ]
        mock_cursor.fetchall.return_value = sample_folders
        mock_sm.read_folder.side_effect = lambda user_id, folder_id: [
            str(f_id)
            for f_id in next(
                f["file_ids"] for f in sample_folders if str(f["id"]) == folder_id
            )
        ]

        folders = await read_folders(mock_cp, mock_sm, user_id)

        self.assertEqual(len(folders), len(sample_folders))
        for folder, sample in zip(folders, sample_folders):
            self.assertIsInstance(folder, Folder)
            self.assertEqual(folder.id, sample["id"])
            self.assertEqual(folder.owner_id, sample["owner_id"])
            self.assertEqual(folder.name, sample["name"])

    async def test_read_folders_with_string_user_id(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        sample_folders = [
            {
                "id": uuid.uuid4(),
                "owner_id": user_id,
                "name": "Folder1",
                "file_ids": [uuid.uuid4()],
            },
            {
                "id": uuid.uuid4(),
                "owner_id": user_id,
                "name": "Folder2",
                "file_ids": [uuid.uuid4()],
            },
        ]
        mock_cursor.fetchall.return_value = sample_folders
        mock_sm.read_folder.side_effect = lambda user_id, folder_id: [
            str(f_id)
            for f_id in next(
                f["file_ids"] for f in sample_folders if str(f["id"]) == folder_id
            )
        ]

        folders = await read_folders(mock_cp, mock_sm, str(user_id))

        self.assertEqual(len(folders), len(sample_folders))
        for folder, sample in zip(folders, sample_folders):
            self.assertIsInstance(folder, Folder)
            self.assertEqual(folder.id, sample["id"])
            self.assertEqual(folder.owner_id, sample["owner_id"])
            self.assertEqual(folder.name, sample["name"])

    async def test_read_folders_no_results(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        mock_cursor.fetchall.return_value = []

        folders = await read_folders(mock_cp, mock_sm, user_id)

        self.assertEqual(folders, [])

    async def test_read_folders_inconsistent_storage(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        sample_folders = [
            {
                "id": folder_id,
                "owner_id": user_id,
                "name": "Folder1",
                "file_ids": [uuid.uuid4()],
            }
        ]
        mock_cursor.fetchall.return_value = sample_folders

        # Simulating inconsistency between DB and Storage
        mock_sm.read_folder.return_value = ["mismatched-file-id"]

        with self.assertRaises(FolderReadError):
            await read_folders(mock_cp, mock_sm, user_id)


class TestReadFolder(unittest.IsolatedAsyncioTestCase):
    async def test_read_folder_success(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
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

        mock_sm.read_folder.return_value = [
            str(f_id) for f_id in sample_folder["file_ids"]
        ]

        folder = await read_folder(mock_cp, mock_sm, user_id, picture_set_id)

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, picture_set_id)
        self.assertEqual(folder.owner_id, user_id)
        self.assertEqual(folder.file_ids, sample_folder["file_ids"])

    async def test_read_folder_not_found(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        picture_set_id = uuid.uuid4()
        mock_cursor.fetchone.return_value = None

        with self.assertRaises(FolderNotFoundError) as context:
            await read_folder(mock_cp, mock_sm, user_id, picture_set_id)

        self.assertIn(f"Folder {picture_set_id} not found", str(context.exception))

    async def test_read_folder_inconsistent_storage(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
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

        mock_sm.read_folder.return_value = ["mismatched-file-id"]

        with self.assertRaises(FolderReadError):
            await read_folder(mock_cp, mock_sm, user_id, picture_set_id)


class TestDeleteFolder(unittest.IsolatedAsyncioTestCase):
    async def test_delete_folder_success(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            {"id": str(folder_id), "owner_id": str(user_id)},  # Folder exists
        ]

        folder = await delete_folder(mock_cp, mock_sm, user_id, folder_id)

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, folder_id)

        mock_sm.delete_folder.assert_called_once_with(str(user_id), str(folder_id))

    async def test_delete_folder_user_not_found(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None  # User not found

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        with self.assertRaises(UserNotFoundError):
            await delete_folder(mock_cp, mock_sm, user_id, folder_id)

    async def test_delete_folder_default_folder(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
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
            await delete_folder(mock_cp, mock_sm, user_id, folder_id)

    async def test_delete_folder_not_found(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
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
            await delete_folder(mock_cp, mock_sm, user_id, folder_id)

    async def test_delete_folder_storage_error(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_sm.delete_folder.side_effect = Exception("Storage error")

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            {"id": str(folder_id), "owner_id": str(user_id)},  # Folder exists
        ]

        with self.assertRaises(FolderDeletionError):
            await delete_folder(mock_cp, mock_sm, user_id, folder_id)


class TestCreateFolder(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        """Generate a valid in-memory image once for all tests."""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        cls.image = img_bytes.getvalue()

    async def test_create_folder_success(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

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
            mock_cp, mock_sm, user_id, files, name="test_folder"
        )

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, folder_id)
        self.assertEqual(len(folder.file_ids), len(files))

        mock_sm.save_file.assert_called()

    async def test_create_folder_user_not_found(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None  # User not found

        user_id = uuid.uuid4()
        files = [self.image]

        with self.assertRaises(UserNotFoundError):
            await create_folder(mock_cp, mock_sm, user_id, files)

    async def test_create_folder_fallback_to_default(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
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

        folder = await create_folder(mock_cp, mock_sm, user_id, files)

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, default_folder_id)
        self.assertEqual(len(folder.file_ids), len(files))

    async def test_create_folder_fails(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
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
            await create_folder(mock_cp, mock_sm, user_id, files)

    async def test_create_folder_file_creation_fails(self):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_sm = MagicMock(spec=StorageManager)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        files = [self.image]

        mock_cursor.fetchone.side_effect = [
            {"id": str(user_id), "default_folder_id": str(uuid.uuid4())},  # User exists
            {"id": str(folder_id), "owner_id": str(user_id)},  # Folder created
            None,  # File creation failed
        ]

        with self.assertRaises(FileCreationError):
            await create_folder(mock_cp, mock_sm, user_id, files)


class TestReadFile(unittest.IsolatedAsyncioTestCase):
    async def test_valid_file_returns_blob(self):
        mock_sm = MagicMock(spec=StorageManager)
        expected_blob = b"sample binary data"
        mock_sm.read_file.return_value = expected_blob

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        file_id = uuid.uuid4()

        blob = await read_file(mock_sm, user_id, folder_id, file_id)

        self.assertEqual(blob, expected_blob)
        mock_sm.read_file.assert_called_once_with(user_id, str(folder_id), str(file_id))

    async def test_file_not_found_raises_error(self):
        mock_sm = MagicMock(spec=StorageManager)
        mock_sm.read_file.side_effect = StorageFileNotFound()

        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        file_id = uuid.uuid4()

        with self.assertRaises(FileNotFoundError):
            await read_file(mock_sm, user_id, folder_id, file_id)

        mock_sm.read_file.assert_called_once_with(user_id, str(folder_id), str(file_id))
