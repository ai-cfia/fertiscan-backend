from abc import ABC, abstractmethod
from io import BytesIO
from uuid import UUID

import filetype
from minio import Minio, S3Error
from pydantic import validate_call

from app.exceptions import StorageFileNotFound
from app.models.files import StorageFile


class StorageManager(ABC):
    @abstractmethod
    def save_file(
        self, namespace: str, file_name: str, file_data: bytes, **kwargs
    ) -> None:
        pass

    @abstractmethod
    def read_file(self, namespace: str, file_name: str, **kwargs) -> StorageFile:
        pass

    @abstractmethod
    def delete_file(self, namespace: str, file_name: str, **kwargs) -> None:
        pass

    @abstractmethod
    def read_folder(self, namespace: str, prefix: str, **kwargs) -> list[str]:
        pass

    @abstractmethod
    def delete_folder(self, namespace: str, prefix: str, **kwargs) -> None:
        pass

    @abstractmethod
    def delete_namespace(self, namespace: str, **kwargs) -> None:
        pass


class MinIOStorageManager(StorageManager):
    def __init__(self, client: Minio):
        self.client = client

    @validate_call
    def save_file(
        self,
        namespace: str,
        file_name: str,
        file_data: bytes,
        content_type: str | None = None,
    ) -> None:
        if not self.client.bucket_exists(namespace):
            self.client.make_bucket(namespace)

        file_stream = BytesIO(file_data)
        if not content_type:
            kind = filetype.guess(file_data)
            content_type = kind.mime if kind else "application/octet-stream"

        self.client.put_object(
            namespace,
            file_name,
            file_stream,
            length=len(file_data),
            content_type=content_type,
        )

    @validate_call
    def read_file(self, namespace: str, file_name: str) -> StorageFile:
        try:
            response = self.client.get_object(namespace, file_name)
            return StorageFile(
                content=response.read(),
                content_type=response.headers.get("Content-Type"),
                length=response.headers.get("Content-Length"),
            )
        except S3Error as e:
            if e.code in {"NoSuchKey", "NoSuchBucket"}:
                raise StorageFileNotFound(f"{e}") from e
            raise

    @validate_call
    def delete_file(self, namespace: str, file_name: str) -> None:
        try:
            self.client.remove_object(namespace, file_name)
        except S3Error as e:
            if e.code == "NoSuchBucket":
                raise StorageFileNotFound(f"{e}") from e
            raise

    @validate_call
    def read_folder(self, namespace: str, prefix: str) -> list[str]:
        objects = self.client.list_objects(namespace, prefix=prefix, recursive=True)
        return [obj.object_name.removeprefix(prefix) for obj in objects]

    @validate_call
    def delete_folder(self, namespace: str, prefix: str) -> None:
        objects_to_delete = self.client.list_objects(
            namespace, prefix=prefix, recursive=True
        )
        for obj in objects_to_delete:
            self.client.remove_object(namespace, obj.object_name)

    @validate_call
    def delete_namespace(self, namespace: str) -> None:
        objects_to_delete = self.client.list_objects(namespace, recursive=True)
        for obj in objects_to_delete:
            self.client.remove_object(namespace, obj.object_name)
        try:
            self.client.remove_bucket(namespace)
        except S3Error as e:
            if e.code == "NoSuchBucket":
                raise StorageFileNotFound(f"{e}") from e
            raise


class FertiscanStorage:
    def __init__(self, sm: StorageManager, namespace: str = "fertiscan"):
        self.sm = sm
        self.namespace = namespace

    @validate_call
    def build_user_path(self, user_id: UUID | None = None) -> str:
        return f"users/{user_id}/" if user_id else "users/"

    @validate_call
    def build_inspection_path(
        self, user_id: UUID, inspection_id: UUID | None = None
    ) -> str:
        return (
            f"{self.build_user_path(user_id)}inspections/{inspection_id}/"
            if inspection_id
            else f"{self.build_user_path(user_id)}inspections/"
        )

    @validate_call
    def build_label_path(
        self,
        user_id: UUID,
        inspection_id: UUID,
        label_id: UUID | None = None,
    ) -> str:
        return (
            f"{self.build_inspection_path(user_id, inspection_id)}labels/{label_id}"
            if label_id
            else f"{self.build_inspection_path(user_id, inspection_id)}labels/"
        )

    @validate_call
    def save_label(
        self,
        user_id: UUID,
        inspection_id: UUID,
        label_id: UUID,
        file_data: bytes,
        content_type: str | None = None,
    ):
        file_path = self.build_label_path(user_id, inspection_id, label_id)
        self.sm.save_file(
            self.namespace, file_path, file_data, content_type=content_type
        )

    @validate_call
    def create_inspection_folder(
        self,
        user_id: UUID,
        inspection_id: UUID,
        labels: dict[UUID, bytes],
    ) -> None:
        for label_id, label_data in labels.items():
            self.save_label(user_id, inspection_id, label_id, label_data)

    @validate_call
    def read_inspection_folder(self, user_id: UUID, inspection_id: UUID):
        folder_path = self.build_label_path(user_id, inspection_id)
        ids = self.sm.read_folder(self.namespace, folder_path)
        return [UUID(id) for id in ids]

    @validate_call
    def read_label(self, user_id: UUID, inspection_id: UUID, label_id: UUID):
        file_path = self.build_label_path(user_id, inspection_id, label_id)
        return self.sm.read_file(self.namespace, file_path)

    @validate_call
    def delete_label(self, user_id: UUID, inspection_id: UUID, label_id: UUID):
        file_path = self.build_label_path(user_id, inspection_id, label_id)
        self.sm.delete_file(self.namespace, file_path)

    @validate_call
    def delete_inspection_folder(self, user_id: UUID, inspection_id: UUID):
        folder_path = self.build_inspection_path(user_id, inspection_id)
        self.sm.delete_folder(self.namespace, folder_path)

    @validate_call
    def delete_user_folder(self, user_id: UUID):
        folder_path = self.build_user_path(user_id)
        self.sm.delete_folder(self.namespace, folder_path)
