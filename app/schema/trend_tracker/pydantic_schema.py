from typing import List
from pydantic import BaseModel, Field
from datetime import datetime


class SearchItem(BaseModel):
    item_name: str = Field(..., description="Name of the item.")
    item_title: str = Field(..., description="Title of the item.")
    item_description: str = Field(..., description="Description of the item.")
    item_source: str = Field(..., description="Source of the item.")


class InputContext(BaseModel):
    content: str = Field(..., description="The content or context provided by the user.")
    timestamp: int = Field(
        ..., description="The timestamp in milliseconds when the input was generated."
    )
    keywords: List[str] = Field(
        ..., description="Array of keywords related to the content."
    )
    related_terms: List[str] = Field(
        ..., description="Array of terms related to what is being searched."
    )
    search_items: List[SearchItem] = Field(
        ..., description="Array of items related to the search."
    )