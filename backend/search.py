# Create a class with pydantic that represents the search query. One of its attributes should be a list of strings called keywords. Another is the label_id. Anohter the user_id. The class should be named SearchQuery.
from typing import List, Optional
from pydantic import BaseModel


class SearchQuery(BaseModel):
    keywords: List[str]
    label_id: Optional[str]
    user_id: Optional[str]
    registration_number: Optional[str]

    class Config:
        populate_by_name = True