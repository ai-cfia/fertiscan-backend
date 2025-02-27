from abc import ABC, abstractmethod
from io import BytesIO
from typing import Callable
from uuid import UUID

import filetype
from minio import Minio, S3Error

from app.exceptions import StorageFileNotFound
from app.models.files import StorageFile


class StorageManager(ABC):
    @abstractmethod
    def save_file(
        self, namespace: str, folder: str, file_name: str, file_data: bytes, **kwargs
    ) -> None:
        pass

    @abstractmethod
    def read_file(
        self, namespace: str, folder: str, file_name: str, **kwargs
    ) -> StorageFile:
        pass

    @abstractmethod
    def delete_file(self, namespace: str, file_name: str, **kwargs) -> None:
        pass

    @abstractmethod
    def read_folder(self, namespace: str, folder: str, **kwargs) -> list[str]:
        pass

    @abstractmethod
    def delete_folder(self, namespace: str, folder: str, **kwargs) -> None:
        pass

    @abstractmethod
    def delete_namespace(self, namespace: str, **kwargs) -> None:
        pass


class MinIOStorageManager(StorageManager):
    def __init__(self, client: Minio, format_ns: Callable[[str], str] = lambda x: x):
        self.client = client
        self.format_ns = format_ns

    def save_file(
        self,
        namespace: str,
        folder: str,
        file_name: str,
        file_data: bytes,
        content_type: str | None = None,
    ) -> None:
        namespace = self.format_ns(namespace)
        if not self.client.bucket_exists(namespace):
            self.client.make_bucket(namespace)
        object_name = f"{folder}/{file_name}" if folder else file_name
        file_stream = BytesIO(file_data)
        if not content_type:
            kind = filetype.guess(file_data)
            content_type = kind.mime if kind else "application/octet-stream"
        self.client.put_object(
            namespace,
            object_name,
            file_stream,
            length=len(file_data),
            content_type=content_type,
        )

    def read_file(self, namespace: str, folder: str, file_name: str):
        namespace = self.format_ns(namespace)
        object_name = f"{folder}/{file_name}" if folder else file_name
        try:
            response = self.client.get_object(namespace, object_name)
            return StorageFile(
                content=response.read(),
                content_type=response.headers.get("Content-Type"),
                length=response.headers.get("Content-Length"),
            )
        except S3Error as e:
            if e.code in {"NoSuchKey", "NoSuchBucket"}:
                raise StorageFileNotFound(f"{e}") from e
            raise

    def delete_file(self, namespace: str, file_name: str) -> None:
        namespace = self.format_ns(namespace)
        try:
            self.client.remove_object(namespace, file_name)
        except S3Error as e:
            if e.code == "NoSuchBucket":
                raise StorageFileNotFound(f"{e}") from e
            raise

    def read_folder(self, namespace: str, folder: str) -> list[str]:
        namespace = self.format_ns(namespace)
        prefix = f"{folder}/"
        objects = self.client.list_objects(namespace, prefix=prefix, recursive=True)
        return [obj.object_name.removeprefix(prefix) for obj in objects]

    def delete_folder(self, namespace: str, folder: str) -> None:
        namespace = self.format_ns(namespace)
        objects_to_delete = self.client.list_objects(
            namespace, prefix=folder, recursive=True
        )
        for obj in objects_to_delete:
            self.client.remove_object(namespace, obj.object_name)

    def delete_namespace(self, namespace: str) -> None:
        namespace = self.format_ns(namespace)
        objects_to_delete = self.client.list_objects(namespace, recursive=True)
        for obj in objects_to_delete:
            self.client.remove_object(namespace, obj.object_name)
        try:
            self.client.remove_bucket(namespace)
        except S3Error as e:
            if e.code == "NoSuchBucket":
                raise StorageFileNotFound(f"{e}") from e
            raise


def build_storage_name(id: UUID, prefix: str = "") -> str:
    if not isinstance(id, UUID):
        id = UUID(id)
    return f"{prefix}-{id}" if prefix else f"{id}"
