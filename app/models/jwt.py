from pydantic import BaseModel

from app.models.users import User

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User