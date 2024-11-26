from typing import List
from pydantic import BaseModel, Field


class FollowUp(BaseModel):
    date: int = Field(..., description="The timestamp in milliseconds for the follow-up date.")
    suggestions: str = Field(..., description="Follow-up suggestions provided.")


class ResponseSchema(BaseModel):
    email: str = Field(..., description="Written email response.")


class InputContext(BaseModel):
    content: str = Field(..., description="The content or context provided by the user.")
    timestamp: int = Field(..., description="The timestamp in milliseconds when the input was generated.")
    response: ResponseSchema = Field(..., description="The response details.")
    follow_up: FollowUp = Field(..., description="Follow-up details, including date and suggestions.")

