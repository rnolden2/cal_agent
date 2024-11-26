from typing import List
from pydantic import BaseModel, Field
from datetime import datetime


class ResponseSchema(BaseModel):
    bullet_points: List[str] = Field(
        ..., 
        description="Array of bullet points, limited to a maximum of 5 items.", 
        max_items=5
    )
    paragraph: str = Field(..., description="A detailed paragraph response.")
    report: str = Field(..., description="A full report provided as part of the response.")


class InputContext(BaseModel):
    content: str = Field(..., description="The content or context provided by the user.")
    timestamp: int = Field(..., description="The timestamp in milliseconds when the input was generated.")
    response: ResponseSchema = Field(..., description="The structured response whether its bullet points, a paragraph, or a report.")
