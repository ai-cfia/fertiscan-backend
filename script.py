from minio import Minio
from app.exceptions import StorageFileNotFound
from app.services.file_storage import MinIOStorage

minio_client = Minio(
    "localhost:9000",
    access_key="gnYGlw5XgV83ngIBOEcg",
    secret_key="hdZrXJPwbJZnsEBMb0fnUEPm0somyXTwNfksJtQj",
    secure=False,
)

storage = MinIOStorage(minio_client)

def test_delete_existing_file():
    namespace = "test-bucket"
    file_name = "delete_test.txt"
    file_content = b"Testing delete_file"
    
    storage.save_file(namespace, "", file_name, file_content)
    storage.delete_file(namespace, file_name)

    try:
        storage.read_file(namespace, "", file_name)
        print("Delete existing file test failed (file should not exist).")
    except StorageFileNotFound:
        print("Delete existing file test passed.")

def test_delete_non_existent_file():
    namespace = "test-bucket"
    file_name = "non_existent.txt"

    try:
        storage.delete_file(namespace, file_name)
        print("Delete non-existent file test passed.")
    except Exception:
        print("Delete non-existent file test failed (should not raise an error).")

def test_delete_file_from_non_existent_bucket():
    namespace = "non-existent-bucket"
    file_name = "test_file.txt"

    try:
        storage.delete_file(namespace, file_name)
        print("Delete file from non-existent bucket test failed (should have raised an error).")
    except Exception:
        print("Delete file from non-existent bucket test passed.")

def test_delete_file_with_special_characters():
    namespace = "test-bucket"
    file_name = "spécial_fïle@#.txt"
    file_content = b"Testing special characters in file name"
    
    storage.save_file(namespace, "", file_name, file_content)
    storage.delete_file(namespace, file_name)

    try:
        storage.read_file(namespace, "", file_name)
        print("Delete file with special characters test failed (file should not exist).")
    except StorageFileNotFound:
        print("Delete file with special characters test passed.")

def test_delete_file_in_nested_folder():
    namespace = "test-bucket"
    folder = "nested/folder"
    file_name = "nested_file.txt"
    file_content = b"Testing nested folder delete"

    storage.save_file(namespace, folder, file_name, file_content)
    storage.delete_file(namespace, f"{folder}/{file_name}")

    try:
        storage.read_file(namespace, folder, file_name)
        print("Delete file in nested folder test failed (file should not exist).")
    except StorageFileNotFound:
        print("Delete file in nested folder test passed.")

def test_delete_file_from_non_existent_folder():
    namespace = "test-bucket"
    folder = "non-existent-folder"
    file_name = "test_file.txt"

    try:
        storage.delete_file(namespace, f"{folder}/{file_name}")
        print("Delete file from non-existent folder test passed.")
    except Exception:
        print("Delete file from non-existent folder test failed (should not raise an error).")


test_delete_existing_file()
test_delete_non_existent_file()
test_delete_file_from_non_existent_bucket()
test_delete_file_with_special_characters()
test_delete_file_in_nested_folder()
test_delete_file_from_non_existent_folder()
