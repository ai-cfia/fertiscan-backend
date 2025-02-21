import unittest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from datastore.blob.azure_storage_api import GetBlobError, build_container_name
from psycopg_pool import ConnectionPool

from app.controllers.files import create_folder, read_file, read_folder
from app.exceptions import FileNotFoundError
from app.models.files import Folder


class TestReadFolder(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.files.get_picture_set_pictures")
    async def test_valid_folder_returns_file_ids(self, mock_get_pictures):
        sample_picture_ids = [{"id": uuid.uuid4()}, {"id": uuid.uuid4()}]
        mock_get_pictures.return_value = sample_picture_ids
        cp = MagicMock()
        user_id = uuid.uuid4()
        picture_set_id = uuid.uuid4()
        file_ids = await read_folder(cp, user_id, picture_set_id)
        self.assertEqual(len(file_ids), 2)
        self.assertEqual(file_ids[0], sample_picture_ids[0]["id"])
        self.assertEqual(file_ids[1], sample_picture_ids[1]["id"])
        mock_get_pictures.assert_called_once()


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


class TestCreateFolder(unittest.IsolatedAsyncioTestCase):
    @patch("app.controllers.files.upload_pictures", new_callable=AsyncMock)
    @patch("app.controllers.files.create_picture_set", new_callable=AsyncMock)
    @patch("app.controllers.files.ContainerClient.from_connection_string")
    async def test_create_folder_success(
        self, mock_container_client, mock_create_picture_set, mock_upload_pictures
    ):
        # Setup mocks
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

        # Call function
        result = await create_folder(mock_cp, connection_string, user_id, label_images)

        # Assertions
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
        # Setup mocks
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

        # Call function
        result = await create_folder(mock_cp, connection_string, user_id, label_images)

        # Assertions
        self.assertIsInstance(result, Folder)
        self.assertEqual(result.id, picture_set_id)
        self.assertEqual(result.file_ids, picture_ids)

        mock_container_client.assert_called_once_with(
            connection_string, container_name=build_container_name(str(user_id))
        )
        mock_create_picture_set.assert_called_once()
        mock_upload_pictures.assert_called_once()
