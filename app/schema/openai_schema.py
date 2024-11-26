from typing import List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class Choice(BaseModel):
    index: int
    message: Message
    logprobs: Optional[dict]  # If logprobs are not always provided
    finish_reason: str


class CompletionTokensDetails(BaseModel):
    reasoning_tokens: int
    accepted_prediction_tokens: int
    rejected_prediction_tokens: int


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    completion_tokens_details: CompletionTokensDetails


class ChatCompletion(BaseModel):
    id: str
    object: str
    created: int
    model: str
    system_fingerprint: str
    choices: List[Choice]
    usage: Usage
