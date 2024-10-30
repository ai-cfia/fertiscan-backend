from pydantic import UUID4, BaseModel


class User(BaseModel):
    id: UUID4 | None = None
    username: str | None = None
