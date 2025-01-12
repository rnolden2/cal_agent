from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any

class AgentModel(BaseModel):
    agent: str
    role: str
    content: str
    agent_schema: Union[Dict, Any]
    additional_context: Optional[str] = None
    topic_id: Optional[str] = None
    user_id: Optional[str] = None


class Provider(str, Enum):  # Enum for provider
    OPENAI = "openai"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"


class AgentCallModel(BaseModel):
    provider: Provider
    model: int 
    response: str = Field(..., min_length=1)
    additional_context: Optional[str] = None
    topic_id: Optional[str] = None
    user_id: str

class ProMentorAgentResponse(BaseModel):
    book_titles: str
    book_published_date: str


class DatabaseModel(BaseModel):
    agent: str
    content: Union[str, Dict]
    topic_id: Optional[str] = None
    user_id: str


class AgentTask(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to handle the task.")
    prompt: str = Field(..., description="Task-specific prompt crafted for the agent.")
    additional_context: str = Field(
        "", description="Optional additional context for the task."
    )


class MasterAgentModel(BaseModel):
    content: str = Field(
        ..., description="The content or context provided by the user."
    )
    timestamp: int = Field(
        ..., description="The timestamp in milliseconds when the input was generated."
    )
    task_description: str = Field(
        ..., description="Summary of tasks derived from context."
    )
    agents_involved: List[str] = Field(
        ..., description="List of agent names involved in the task. Agents are"
    )
    tasks: List[AgentTask] = Field(
        ..., description="Tasks routed to individual agents."
    )

class UpdateAgentRequest(BaseModel):
    api_route: str = None
    description: str = None
    description_full: str = None
    last_updated: str = None
    role: str = None
    schema: str = None