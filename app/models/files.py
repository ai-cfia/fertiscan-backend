from datetime import date
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
