from datetime import date, datetime
from uuid import UUID

from datastore.db.metadata.validator import AuditTrail
from pydantic import AliasChoices, AliasPath, BaseModel, Field


class FolderMetadata(BaseModel):
    file_count: int = Field(
        ...,
        validation_alias=AliasChoices(
            "file_count", AliasPath("image_data_picture_set", "number_of_images")
        ),
    )
    audit_trail: AuditTrail


class Folder(BaseModel):
    id: UUID | None = None
    metadata: FolderMetadata | None = Field(
        None, validation_alias=AliasChoices("metadata", "picture_set")
    )
    owner_id: UUID | None = None
    upload_date: date | None = None
    name: str | None = None
    file_ids: list[UUID] | None = []


class FolderResponse(Folder):
    id: UUID


class DeleteFolderResponse(Folder):
    id: UUID
    deleted: bool = True


class UploadedFile(BaseModel):
    id: UUID | None = None
    metadata: dict | None = Field(
        None, validation_alias=AliasChoices("metadata", "picture")
    )
    nb_obj: int | None = None
    picture_set_id: UUID | None = None
    verified: bool = False
    upload_date: datetime | None = None


class StorageFile(BaseModel):
    content: bytes | None = None
    content_type: str | None = None
    length: int | None = None
