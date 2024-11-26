from typing import List
from pydantic import BaseModel, Field


class Article(BaseModel):
    source_name: str = Field(..., description="Name of the source for the article.")
    link: str = Field(..., description="Link to the article.")


class CompetitorData(BaseModel):
    name: str = Field(..., description="Name of the competitor.")
    location: str = Field(..., description="Location of the competitor.")
    website: str = Field(..., description="Website of the competitor.")
    description: str = Field(..., description="Description of the competitor.")
    competitive_product: str = Field(..., description="Competitor's product that competes with yours.")
    articles: List[Article] = Field(..., description="Array of articles related to the competitor.")


class InputContext(BaseModel):
    content: str = Field(..., description="The content or context provided by the user.")
    timestamp: int = Field(
        ..., description="The timestamp in milliseconds when the input was generated."
    )
    competitor_data: CompetitorData = Field(
        ..., description="Details of a competitor, including related articles."
    )
