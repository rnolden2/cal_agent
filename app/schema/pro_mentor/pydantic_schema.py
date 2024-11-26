from typing import List
from pydantic import BaseModel, Field


class InputContext(BaseModel):
    content: str = Field(..., description="The content or context provided by the user.")
    timestamp: int = Field(
        ..., description="The timestamp in milliseconds when the input was generated."
    )


class ImprovementDetails(BaseModel):
    explanation: str = Field(..., description="Explanation of how to improve.")
    actions: List[str] = Field(
        ..., 
        description="Array of actionable steps, limited to 10 items.",
        max_items=10
    )


class Improvement(BaseModel):
    personally: ImprovementDetails = Field(..., description="Suggestions for personal improvement.")
    professionally: ImprovementDetails = Field(..., description="Suggestions for professional improvement.")


class ResponseSchema(BaseModel):
    input_context: InputContext = Field(..., description="Contextual information provided as input.")
    improvement: Improvement = Field(
        ..., description="How the user can improve personally and professionally."
    )
    past_feedback: str = Field(
        ..., description="Explanation of how the input relates to previous feedback."
    )