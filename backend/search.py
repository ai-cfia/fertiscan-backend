# Create a class with pydantic that represents the search query. One of its attributes should be a list of strings called keywords. Another is the label_id. Anohter the user_id. The class should be named SearchQuery.
from typing import Optional
from pydantic import BaseModel


class SearchQuery(BaseModel):
    user_id: Optional[str]
    label_id: Optional[str]

    class Config:
        populate_by_name = True
