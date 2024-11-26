from pydantic import BaseModel, Field
from typing import Dict, Union, Any

class AgentModel(BaseModel):
    role: str
    content: str
    agent_schema: Union[Dict, Any]

class AgentCallModel(BaseModel):
    provider:int
    response:str

class ProMentorAgentResponse(BaseModel):
    book_titles:str
    book_published_date:str


