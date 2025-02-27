import unittest
from functools import partial
from unittest.mock import ANY, MagicMock, patch
from uuid import uuid4

from minio import S3Error

from app.exceptions import StorageFileNotFound
from app.models.files import StorageFile
from app.services.file_storage import MinIOStorageManager, build_storage_name


class TestMinIOSaveFile(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.put_object = MagicMock()
        self.mock_minio_client.bucket_exists = MagicMock(return_value=True)
        self.raw_namespace = str(uuid4())
        self.format_ns = partial(build_storage_name, prefix="test-bucket")
        self.namespace = self.format_ns(self.raw_namespace)
        self.storage_manager = MinIOStorageManager(
            self.mock_minio_client, format_ns=self.format_ns
        )
        self.folder = "test-folder"
        self.file_name = "test.txt"
        self.file_data = b"Hello, World!"

    def test_save_file(self):
        for folder in [self.folder, ""]:
            with self.subTest(folder=folder):
                self.storage_manager.save_file(
                    self.raw_namespace, folder, self.file_name, self.file_data
                )
                self.mock_minio_client.put_object.assert_called_with(
                    self.namespace,
                    f"{folder}/{self.file_name}" if folder else self.file_name,
                    ANY,
                    length=len(self.file_data),
                    content_type=ANY,
                )

    @patch("filetype.guess")
    def test_save_file_detects_content_type(self, mock_filetype_guess):
        mock_filetype_guess.return_value = MagicMock(mime="text/plain")
        self.storage_manager.save_file(
            self.raw_namespace, self.folder, self.file_name, self.file_data
        )
        self.mock_minio_client.put_object.assert_called_once_with(
            self.namespace,
            f"{self.folder}/{self.file_name}",
            ANY,
            length=len(self.file_data),
            content_type="text/plain",
        )

    def test_save_file_with_explicit_content_type(self):
        content_type = "text/plain"
        self.storage_manager.save_file(
            self.raw_namespace,
            self.folder,
            self.file_name,
            self.file_data,
            content_type,
        )
        self.mock_minio_client.put_object.assert_called_once_with(
            self.namespace,
            f"{self.folder}/{self.file_name}",
            ANY,
            length=len(self.file_data),
            content_type=content_type,
        )

    def test_save_file_handles_s3_error(self):
        self.mock_minio_client.put_object.side_effect = S3Error(
            "S3Error", "Mock error", "400", "request_id", "host_id", "response"
        )
        with self.assertRaises(S3Error):
            self.storage_manager.save_file(
                self.raw_namespace, self.folder, self.file_name, self.file_data
            )


class TestMinIOReadFile(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.get_object = MagicMock()
        self.raw_namespace = str(uuid4())
        self.format_ns = partial(build_storage_name, prefix="test-bucket")
        self.namespace = self.format_ns(self.raw_namespace)
        self.storage_manager = MinIOStorageManager(
            self.mock_minio_client, format_ns=self.format_ns
        )
        self.folder = "test-folder"
        self.file_name = "test.txt"

    def test_read_file_successfully(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"File content"
        mock_response.headers = {"Content-Type": "text/plain", "Content-Length": "12"}

        self.mock_minio_client.get_object.return_value = mock_response

        result = self.storage_manager.read_file(
            self.raw_namespace, self.folder, self.file_name
        )

        self.mock_minio_client.get_object.assert_called_once_with(
            self.namespace, f"{self.folder}/{self.file_name}"
        )
        self.assertIsInstance(result, StorageFile)
        self.assertEqual(result.content, b"File content")
        self.assertEqual(result.content_type, "text/plain")
        self.assertEqual(result.length, 12)

    def test_read_file_not_found(self):
        self.mock_minio_client.get_object.side_effect = S3Error(
            "NoSuchKey", "Mock error", "404", "request_id", "host_id", "response"
        )

        with self.assertRaises(StorageFileNotFound):
            self.storage_manager.read_file(
                self.raw_namespace, self.folder, self.file_name
            )

    def test_read_file_bucket_not_found(self):
        self.mock_minio_client.get_object.side_effect = S3Error(
            "NoSuchBucket", "Mock error", "404", "request_id", "host_id", "response"
        )

        with self.assertRaises(StorageFileNotFound):
            self.storage_manager.read_file(
                self.raw_namespace, self.folder, self.file_name
            )


class TestMinIODeleteFile(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.remove_object = MagicMock()
        self.raw_namespace = str(uuid4())
        self.format_ns = partial(build_storage_name, prefix="test-bucket")
        self.namespace = self.format_ns(self.raw_namespace)
        self.storage_manager = MinIOStorageManager(
            self.mock_minio_client, format_ns=self.format_ns
        )
        self.file_name = "test.txt"

    def test_delete_file_successfully(self):
        self.storage_manager.delete_file(self.raw_namespace, self.file_name)
        self.mock_minio_client.remove_object.assert_called_once_with(
            self.namespace, self.file_name
        )

    def test_delete_file_not_found(self):
        self.mock_minio_client.remove_object.side_effect = S3Error(
            "NoSuchBucket", "Mock error", "404", "request_id", "host_id", "response"
        )

        with self.assertRaises(StorageFileNotFound):
            self.storage_manager.delete_file(self.raw_namespace, self.file_name)


class TestMinIOReadFolder(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.list_objects = MagicMock()
        self.raw_namespace = str(uuid4())
        self.format_ns = partial(build_storage_name, prefix="test-bucket")
        self.namespace = self.format_ns(self.raw_namespace)
        self.storage_manager = MinIOStorageManager(
            self.mock_minio_client, format_ns=self.format_ns
        )
        self.folder = "test-folder"

    def test_read_folder_successfully(self):
        self.mock_minio_client.list_objects.return_value = [
            MagicMock(object_name="test-folder/file1.txt"),
            MagicMock(object_name="test-folder/file2.txt"),
        ]

        result = self.storage_manager.read_folder(self.raw_namespace, self.folder)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=f"{self.folder}/", recursive=True
        )
        self.assertEqual(result, ["file1.txt", "file2.txt"])

    def test_read_folder_empty(self):
        self.mock_minio_client.list_objects.return_value = []

        result = self.storage_manager.read_folder(self.raw_namespace, self.folder)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=f"{self.folder}/", recursive=True
        )
        self.assertEqual(result, [])


class TestMinIODeleteFolder(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.list_objects = MagicMock()
        self.mock_minio_client.remove_object = MagicMock()
        self.raw_namespace = str(uuid4())
        self.format_ns = partial(build_storage_name, prefix="test-bucket")
        self.namespace = self.format_ns(self.raw_namespace)
        self.storage_manager = MinIOStorageManager(
            self.mock_minio_client, format_ns=self.format_ns
        )
        self.folder = "test-folder"

    def test_delete_folder_successfully(self):
        self.mock_minio_client.list_objects.return_value = [
            MagicMock(object_name="test-folder/file1.txt"),
            MagicMock(object_name="test-folder/file2.txt"),
        ]

        self.storage_manager.delete_folder(self.raw_namespace, self.folder)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=self.folder, recursive=True
        )
        self.mock_minio_client.remove_object.assert_any_call(
            self.namespace, "test-folder/file1.txt"
        )
        self.mock_minio_client.remove_object.assert_any_call(
            self.namespace, "test-folder/file2.txt"
        )
        self.assertEqual(self.mock_minio_client.remove_object.call_count, 2)

    def test_delete_folder_empty(self):
        self.mock_minio_client.list_objects.return_value = []

        self.storage_manager.delete_folder(self.raw_namespace, self.folder)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=self.folder, recursive=True
        )
        self.mock_minio_client.remove_object.assert_not_called()


class TestMinIODeleteNamespace(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.list_objects = MagicMock()
        self.mock_minio_client.remove_object = MagicMock()
        self.mock_minio_client.remove_bucket = MagicMock()
        self.raw_namespace = str(uuid4())
        self.format_ns = partial(build_storage_name, prefix="test-bucket")
        self.namespace = self.format_ns(self.raw_namespace)
        self.storage_manager = MinIOStorageManager(
            self.mock_minio_client, format_ns=self.format_ns
        )

    def test_delete_namespace_successfully(self):
        self.mock_minio_client.list_objects.return_value = [
            MagicMock(object_name="file1.txt"),
            MagicMock(object_name="file2.txt"),
        ]

        self.storage_manager.delete_namespace(self.raw_namespace)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, recursive=True
        )
        self.mock_minio_client.remove_object.assert_any_call(
            self.namespace, "file1.txt"
        )
        self.mock_minio_client.remove_object.assert_any_call(
            self.namespace, "file2.txt"
        )
        self.mock_minio_client.remove_bucket.assert_called_once_with(self.namespace)

    def test_delete_namespace_empty(self):
        self.mock_minio_client.list_objects.return_value = []

        self.storage_manager.delete_namespace(self.raw_namespace)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, recursive=True
        )
        self.mock_minio_client.remove_object.assert_not_called()
        self.mock_minio_client.remove_bucket.assert_called_once_with(self.namespace)

    def test_delete_namespace_not_found(self):
        self.mock_minio_client.remove_bucket.side_effect = S3Error(
            "NoSuchBucket", "Mock error", "404", "request_id", "host_id", "response"
        )

        with self.assertRaises(StorageFileNotFound):
            self.storage_manager.delete_namespace(self.raw_namespace)
