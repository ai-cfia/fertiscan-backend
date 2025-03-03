from datetime import datetime
from uuid import UUID

from pydantic import UUID4, AliasChoices, BaseModel, Field


class User(BaseModel):
    id: UUID4 | None = None
    username: str | None = Field(
        None, validation_alias=AliasChoices("username", "email")
    )
    registration_date: datetime | None = None
    updated_at: datetime | None = None
    default_folder_id: UUID | None = Field(
        None,
        validation_alias=AliasChoices("default_folder_id", "default_set_id"),
    )
