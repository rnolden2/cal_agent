from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Any
from datetime import datetime


class AgentModel(BaseModel):
    agent: str
    role: str
    content: str
    agent_schema: Union[Dict, Any]
    additional_context: Optional[str] = None
    model: Optional[int] = None
    provider: Optional[str] = None
    topic_id: Optional[str] = None
    user_id: Optional[str] = None


class Provider(str, Enum):  # Enum for provider
    OPENAI = "openai"
    GOOGLE = "google"
    PERPLEXITY = "perplexity"
    XAI = "xai"


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
    content: Union[str, Dict]
    topic_id: Optional[str] = None
    user_id: str
    agent_name: Optional[str] = None


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
    agent_schema: str = None


class FeedbackModel(BaseModel):
    feedback_text: str = Field(..., description="The feedback content from your boss")
    category: str = Field(..., description="Category of feedback (e.g., presentation_skills, technical_accuracy)")
    user_id: str = Field(..., description="User ID who received the feedback")
    source: Optional[str] = Field(default="boss_feedback", description="Source of the feedback")
    context: Optional[str] = Field(default=None, description="Context where feedback was given (e.g., Army presentation)")
    agent_name: Optional[str] = Field(default=None, description="Specific agent this feedback applies to")
    topic_id: Optional[str] = Field(default=None, description="Topic ID if related to a specific conversation")
    rating: Optional[int] = Field(default=None, description="Optional rating from 1-5")


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: Optional[str] = None


class ReportSection(BaseModel):
    section_id: str = Field(..., description="Unique identifier for the section")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in markdown")
    status: str = Field(default="draft", description="Section status: draft, completed, needs_revision")
    agent_contributors: List[str] = Field(default_factory=list, description="Agents that contributed to this section")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")


class ReportModel(BaseModel):
    title: str = Field(..., description="Report title")
    description: Optional[str] = Field(default=None, description="Report description")
    user_id: str = Field(..., description="User who created the report")
    sections: List[ReportSection] = Field(default_factory=list, description="Report sections")
    status: str = Field(default="draft", description="Report status: draft, completed, published")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")


class ReportGenerationRequest(BaseModel):
    title: str = Field(..., description="Report title")
    description: Optional[str] = Field(default=None, description="Report description or requirements")
    user_id: str = Field(..., description="User ID")
    sections_to_generate: List[str] = Field(default_factory=list, description="Specific sections to generate")


class ReportResponse(BaseModel):
    success: bool
    message: str
    report_id: Optional[str] = None
    report: Optional[ReportModel] = None


class SectionUpdateRequest(BaseModel):
    section_id: str = Field(..., description="Section ID to update")
    feedback: str = Field(..., description="Feedback for section improvement")
    user_id: str = Field(..., description="User ID")
