import os
import unittest
from unittest.mock import ANY, MagicMock, patch
from uuid import uuid4

from dotenv import load_dotenv
from minio import Minio, S3Error

from app.exceptions import StorageFileNotFound
from app.models.files import StorageFile
from app.services.file_storage import FertiscanStorage, MinIOStorageManager

load_dotenv(".env.config")


class TestMinIOSaveFile(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.put_object = MagicMock()
        self.mock_minio_client.bucket_exists = MagicMock(return_value=True)
        self.namespace = "test-namespace"
        self.storage_manager = MinIOStorageManager(self.mock_minio_client)
        self.file_name = "test.txt"
        self.file_data = b"Hello, World!"

    def test_save_file(self):
        self.storage_manager.save_file(self.namespace, self.file_name, self.file_data)
        self.mock_minio_client.put_object.assert_called_with(
            self.namespace,
            self.file_name,
            ANY,
            length=len(self.file_data),
            content_type=ANY,
        )

    @patch("filetype.guess")
    def test_save_file_detects_content_type(self, mock_filetype_guess):
        mock_filetype_guess.return_value = MagicMock(mime="text/plain")
        self.storage_manager.save_file(self.namespace, self.file_name, self.file_data)
        self.mock_minio_client.put_object.assert_called_once_with(
            self.namespace,
            self.file_name,
            ANY,
            length=len(self.file_data),
            content_type="text/plain",
        )

    def test_save_file_with_explicit_content_type(self):
        content_type = "text/plain"
        self.storage_manager.save_file(
            self.namespace, self.file_name, self.file_data, content_type
        )
        self.mock_minio_client.put_object.assert_called_once_with(
            self.namespace,
            self.file_name,
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
                self.namespace, self.file_name, self.file_data
            )


class TestMinIOReadFile(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.get_object = MagicMock()
        self.namespace = "test-namespace"
        self.storage_manager = MinIOStorageManager(self.mock_minio_client)
        self.file_name = "test.txt"

    def test_read_file_successfully(self):
        mock_response = MagicMock()
        mock_response.read.return_value = b"File content"
        mock_response.headers = {"Content-Type": "text/plain", "Content-Length": "12"}

        self.mock_minio_client.get_object.return_value = mock_response

        result = self.storage_manager.read_file(self.namespace, self.file_name)

        self.mock_minio_client.get_object.assert_called_once_with(
            self.namespace, self.file_name
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
            self.storage_manager.read_file(self.namespace, self.file_name)

    def test_read_file_bucket_not_found(self):
        self.mock_minio_client.get_object.side_effect = S3Error(
            "NoSuchBucket", "Mock error", "404", "request_id", "host_id", "response"
        )

        with self.assertRaises(StorageFileNotFound):
            self.storage_manager.read_file(self.namespace, self.file_name)


class TestMinIODeleteFile(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.remove_object = MagicMock()
        self.namespace = "test-namespace"
        self.storage_manager = MinIOStorageManager(self.mock_minio_client)
        self.file_name = "test.txt"

    def test_delete_file_successfully(self):
        self.storage_manager.delete_file(self.namespace, self.file_name)
        self.mock_minio_client.remove_object.assert_called_once_with(
            self.namespace, self.file_name
        )

    def test_delete_file_not_found(self):
        self.mock_minio_client.remove_object.side_effect = S3Error(
            "NoSuchBucket", "Mock error", "404", "request_id", "host_id", "response"
        )

        with self.assertRaises(StorageFileNotFound):
            self.storage_manager.delete_file(self.namespace, self.file_name)


class TestMinIOReadFolder(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.list_objects = MagicMock()
        self.namespace = "test-namespace"
        self.storage_manager = MinIOStorageManager(self.mock_minio_client)
        self.prefix = "test-folder/"

    def test_read_folder_successfully(self):
        self.mock_minio_client.list_objects.return_value = [
            MagicMock(object_name="test-folder/file1.txt"),
            MagicMock(object_name="test-folder/file2.txt"),
        ]

        result = self.storage_manager.read_folder(self.namespace, self.prefix)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=self.prefix, recursive=True
        )
        self.assertEqual(result, ["file1.txt", "file2.txt"])

    def test_read_folder_empty(self):
        self.mock_minio_client.list_objects.return_value = []

        result = self.storage_manager.read_folder(self.namespace, self.prefix)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=self.prefix, recursive=True
        )
        self.assertEqual(result, [])


class TestMinIODeleteFolder(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.list_objects = MagicMock()
        self.mock_minio_client.remove_object = MagicMock()
        self.namespace = "test-namespace"
        self.storage_manager = MinIOStorageManager(self.mock_minio_client)
        self.prefix = "test-folder/"

    def test_delete_folder_successfully(self):
        self.mock_minio_client.list_objects.return_value = [
            MagicMock(object_name="test-folder/file1.txt"),
            MagicMock(object_name="test-folder/file2.txt"),
        ]

        self.storage_manager.delete_folder(self.namespace, self.prefix)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=self.prefix, recursive=True
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

        self.storage_manager.delete_folder(self.namespace, self.prefix)

        self.mock_minio_client.list_objects.assert_called_once_with(
            self.namespace, prefix=self.prefix, recursive=True
        )
        self.mock_minio_client.remove_object.assert_not_called()


class TestMinIODeleteNamespace(unittest.TestCase):
    def setUp(self):
        self.mock_minio_client = MagicMock()
        self.mock_minio_client.list_objects = MagicMock()
        self.mock_minio_client.remove_object = MagicMock()
        self.mock_minio_client.remove_bucket = MagicMock()
        self.namespace = "test-namespace"
        self.storage_manager = MinIOStorageManager(self.mock_minio_client)

    def test_delete_namespace_successfully(self):
        self.mock_minio_client.list_objects.return_value = [
            MagicMock(object_name="file1.txt"),
            MagicMock(object_name="file2.txt"),
        ]

        self.storage_manager.delete_namespace(self.namespace)

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

        self.storage_manager.delete_namespace(self.namespace)

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
            self.storage_manager.delete_namespace(self.namespace)


@unittest.skipIf(
    os.getenv("INTEGRATION_TESTS", "false").lower() == "false",
    "Skipping save_label tests",
)
class TestFertiscanStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_namespace = "fertiscan-test"
        cls.client = Minio(
            "localhost:9000",
            access_key="minioadmin",
            secret_key="minioadmin",
            secure=False,
        )
        cls.storage_manager = MinIOStorageManager(cls.client)
        cls.storage = FertiscanStorage(
            cls.storage_manager, namespace=cls.test_namespace
        )

    @classmethod
    def tearDownClass(cls):
        try:
            cls.storage_manager.delete_namespace(cls.test_namespace)
        except StorageFileNotFound:
            pass

    def setUp(self):
        self.user_id = uuid4()
        self.inspection_id = uuid4()
        self.label_id = uuid4()
        self.file_data = b"test file content"

    def test_save_label(self):
        self.storage.save_label(
            self.user_id, self.inspection_id, self.label_id, self.file_data
        )
        stored_file = self.storage.read_label(
            self.user_id, self.inspection_id, self.label_id
        )
        self.assertEqual(stored_file.content, self.file_data)

    def test_save_label_with_explicit_content_type(self):
        self.storage.save_label(
            self.user_id,
            self.inspection_id,
            self.label_id,
            self.file_data,
            content_type="text/plain",
        )
        stored_file = self.storage.read_label(
            self.user_id, self.inspection_id, self.label_id
        )
        self.assertEqual(stored_file.content_type, "text/plain")

    def test_save_label_without_content_type(self):
        self.storage.save_label(
            self.user_id, self.inspection_id, self.label_id, self.file_data
        )
        stored_file = self.storage.read_label(
            self.user_id, self.inspection_id, self.label_id
        )
        self.assertIsNotNone(stored_file.content_type)

    def test_save_label_creates_namespace(self):
        new_namespace = "nonexistent-namespace"
        temp_storage = FertiscanStorage(self.storage_manager, namespace=new_namespace)
        temp_storage.save_label(
            self.user_id, self.inspection_id, self.label_id, self.file_data
        )
        stored_file = temp_storage.read_label(
            self.user_id, self.inspection_id, self.label_id
        )
        self.assertEqual(stored_file.content, self.file_data)
        self.storage_manager.delete_namespace(new_namespace)


class TestFertiscanStorageBuildPath(unittest.TestCase):
    def setUp(self):
        self.storage = FertiscanStorage(sm=None)

    def test_build_user_folder_path(self):
        user_id = uuid4()
        expected_path = f"users/{user_id}/"
        self.assertEqual(self.storage.build_user_path(user_id), expected_path)

    def test_build_inspection_folder_path(self):
        user_id = uuid4()
        inspection_id = uuid4()
        expected_path = f"users/{user_id}/inspections/{inspection_id}/"
        self.assertEqual(
            self.storage.build_inspection_path(user_id, inspection_id), expected_path
        )

    def test_build_label_path(self):
        user_id = uuid4()
        inspection_id = uuid4()
        label_id = uuid4()
        expected_path = f"users/{user_id}/inspections/{inspection_id}/labels/{label_id}"
        self.assertEqual(
            self.storage.build_label_path(user_id, inspection_id, label_id),
            expected_path,
        )

    def test_build_inspection_path_without_id(self):
        user_id = uuid4()
        expected_path = f"users/{user_id}/inspections/"
        self.assertEqual(self.storage.build_inspection_path(user_id), expected_path)

    def test_build_label_path_without_id(self):
        user_id = uuid4()
        inspection_id = uuid4()
        expected_path = f"users/{user_id}/inspections/{inspection_id}/labels/"
        self.assertEqual(
            self.storage.build_label_path(user_id, inspection_id), expected_path
        )

    def test_build_path_raises_for_invalid_user_id(self):
        with self.assertRaises(ValueError):
            self.storage.build_user_path("invalid-uuid")

    def test_build_inspection_path_raises_for_invalid_user_id(self):
        with self.assertRaises(ValueError):
            self.storage.build_inspection_path("invalid-uuid")

    def test_build_inspection_path_raises_for_invalid_inspection_id(self):
        user_id = uuid4()
        with self.assertRaises(ValueError):
            self.storage.build_inspection_path(user_id, "invalid-uuid")

    def test_build_label_path_raises_for_invalid_user_id(self):
        with self.assertRaises(ValueError):
            self.storage.build_label_path("invalid-uuid", uuid4())

    def test_build_label_path_raises_for_invalid_inspection_id(self):
        user_id = uuid4()
        with self.assertRaises(ValueError):
            self.storage.build_label_path(user_id, "invalid-uuid", uuid4())

    def test_build_label_path_raises_for_invalid_label_id(self):
        user_id = uuid4()
        inspection_id = uuid4()
        with self.assertRaises(ValueError):
            self.storage.build_label_path(user_id, inspection_id, "invalid-uuid")
