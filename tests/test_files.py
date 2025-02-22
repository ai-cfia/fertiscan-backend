import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from datastore.blob.azure_storage_api import GetBlobError, build_container_name
from psycopg_pool import ConnectionPool

from app.controllers.files import (
    create_folder,
    delete_folder,
    read_file,
    read_folder,
    read_folders,
)
from app.exceptions import FileNotFoundError
from app.models.files import Folder
from datastore.db.queries.picture import PictureSetNotFoundError


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

        with self.assertRaises(FileNotFoundError) as context:
            await read_folder(mock_cp, user_id, picture_set_id)

        self.assertIn(f"Folder {picture_set_id} not found", str(context.exception))


class TestDeleteFolder(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.files.delete_picture_set_permanently")
    @patch("app.controllers.files.ContainerClient.from_connection_string")
    async def test_delete_folder_success(
        self, mock_container_client, mock_delete_picture_set
    ):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_container_client.return_value = MagicMock()
        mock_delete_picture_set.return_value = None

        connection_string = "fake_conn_str"
        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        folder = await delete_folder(mock_cp, connection_string, user_id, folder_id)

        self.assertIsInstance(folder, Folder)
        self.assertEqual(folder.id, folder_id)

        mock_container_client.assert_called_once_with(
            connection_string, container_name=build_container_name(str(user_id))
        )
        mock_delete_picture_set.assert_called_once_with(
            mock_cursor, str(user_id), folder_id, mock_container_client.return_value
        )

    @patch("app.controllers.files.delete_picture_set_permanently")
    @patch("app.controllers.files.ContainerClient.from_connection_string")
    async def test_delete_folder_not_found(
        self, mock_container_client, mock_delete_picture_set
    ):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_container_client.return_value = MagicMock()
        mock_delete_picture_set.side_effect = PictureSetNotFoundError()

        connection_string = "fake_conn_str"
        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()

        with self.assertRaises(FileNotFoundError) as context:
            await delete_folder(mock_cp, connection_string, user_id, folder_id)

        self.assertIn(f"Folder not found with ID: {folder_id}", str(context.exception))

        mock_container_client.assert_called_once_with(
            connection_string, container_name=build_container_name(str(user_id))
        )
        mock_delete_picture_set.assert_called_once_with(
            mock_cursor, str(user_id), folder_id, mock_container_client.return_value
        )


class TestCreateFolder(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.files.upload_pictures", new_callable=AsyncMock)
    @patch("app.controllers.files.create_picture_set", new_callable=AsyncMock)
    @patch("app.controllers.files.ContainerClient.from_connection_string")
    async def test_create_folder_success(
        self, mock_container_client, mock_create_picture_set, mock_upload_pictures
    ):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_container_client.return_value = MagicMock()
        picture_set_id = uuid.uuid4()
        picture_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_create_picture_set.return_value = picture_set_id
        mock_upload_pictures.return_value = picture_ids

        connection_string = "fake_conn_str"
        user_id = uuid.uuid4()
        label_images = [b"image1", b"image2"]

        result = await create_folder(mock_cp, connection_string, user_id, label_images)

        self.assertIsInstance(result, Folder)
        self.assertEqual(result.id, picture_set_id)
        self.assertEqual(result.file_ids, picture_ids)
        self.assertIsNone(result.metadata)
        self.assertIsNone(result.owner_id)
        self.assertIsNone(result.upload_date)
        self.assertIsNone(result.name)

        mock_container_client.assert_called_once_with(
            connection_string, container_name=build_container_name(str(user_id))
        )
        mock_create_picture_set.assert_called_once_with(
            mock_cursor, mock_container_client.return_value, len(label_images), user_id
        )
        mock_upload_pictures.assert_called_once_with(
            mock_cursor,
            str(user_id),
            label_images,
            mock_container_client.return_value,
            str(picture_set_id),
        )

    @patch("app.controllers.files.upload_pictures", new_callable=AsyncMock)
    @patch("app.controllers.files.create_picture_set", new_callable=AsyncMock)
    @patch("app.controllers.files.ContainerClient.from_connection_string")
    async def test_create_folder_invalid_user_id(
        self, mock_container_client, mock_create_picture_set, mock_upload_pictures
    ):
        mock_cp = MagicMock(spec=ConnectionPool)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cp.connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_container_client.return_value = MagicMock()
        picture_set_id = uuid.uuid4()
        picture_ids = [uuid.uuid4(), uuid.uuid4()]
        mock_create_picture_set.return_value = picture_set_id
        mock_upload_pictures.return_value = picture_ids

        connection_string = "fake_conn_str"
        user_id = str(uuid.uuid4())
        label_images = [b"image1", b"image2"]

        result = await create_folder(mock_cp, connection_string, user_id, label_images)

        self.assertIsInstance(result, Folder)
        self.assertEqual(result.id, picture_set_id)
        self.assertEqual(result.file_ids, picture_ids)

        mock_container_client.assert_called_once_with(
            connection_string, container_name=build_container_name(str(user_id))
        )
        mock_create_picture_set.assert_called_once()
        mock_upload_pictures.assert_called_once()


class TestReadFile(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.files.get_blob", new_callable=AsyncMock)
    @patch("app.controllers.files.ContainerClient.from_connection_string")
    async def test_valid_file_returns_blob(self, mock_container_client, mock_get_blob):
        expected_blob = b"sample binary data"
        mock_get_blob.return_value = expected_blob
        container_client_instance = mock_container_client.return_value
        connection_string = "fake_conn_str"
        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        file_id = uuid.uuid4()
        blob = await read_file(connection_string, user_id, folder_id, file_id)
        self.assertEqual(blob, expected_blob)
        mock_container_client.assert_called_once_with(
            connection_string, container_name=build_container_name(str(user_id))
        )
        mock_get_blob.assert_called_once_with(
            container_client_instance, f"{folder_id}/{file_id}"
        )

    @patch("app.controllers.files.get_blob", new_callable=AsyncMock)
    @patch("app.controllers.files.ContainerClient.from_connection_string")
    async def test_file_not_found_raises_error(
        self, mock_container_client, mock_get_blob
    ):
        mock_get_blob.side_effect = GetBlobError("The specified blob does not exist.")
        connection_string = "fake_conn_str"
        user_id = uuid.uuid4()
        folder_id = uuid.uuid4()
        file_id = uuid.uuid4()
        with self.assertRaises(FileNotFoundError) as context:
            await read_file(connection_string, user_id, folder_id, file_id)
        self.assertIn(
            f"File {file_id} not found in folder {folder_id}", str(context.exception)
        )
