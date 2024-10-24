import uuid

from pydantic import UUID4, BaseModel, Field


class ItemCreate(BaseModel):
    name: str
    description: str | None = None


class ItemDB(ItemCreate):
    id: UUID4 = Field(default_factory=uuid.uuid4)


class ItemResponse(ItemCreate):
    id: UUID4
