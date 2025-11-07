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
    enable_verification: bool = Field(default=True, description="Enable fact verification and quality assurance")
    

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


class AgentContribution(BaseModel):
    """Individual agent's contribution to a report section"""
    agent_name: str = Field(..., description="Name of the agent")
    agent_role: str = Field(..., description="Agent's role in section: primary, verification, business_analysis, etc.")
    content: str = Field(..., description="Agent's markdown response content")
    quality_score: float = Field(default=0.0, description="Quality assessment score (0-1)")
    verification_status: str = Field(default="unverified", description="Verification status: verified, unverified, needs_review")
    timestamp: Optional[datetime] = Field(default=None, description="When this contribution was generated")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider used (openai, google, perplexity, xai)")
    llm_model: Optional[str] = Field(default=None, description="Specific model used")
    word_count: int = Field(default=0, description="Word count of content")
    token_count: Optional[int] = Field(default=None, description="Approximate token count")
    feedback_applied: List[str] = Field(default_factory=list, description="List of feedback items applied")


class ReportSection(BaseModel):
    section_id: str = Field(..., description="Unique identifier for the section")
    title: str = Field(..., description="Section title")
    
    # Hybrid storage: individual contributions + synthesized view
    agent_contributions: List[AgentContribution] = Field(
        default_factory=list, 
        description="Individual agent contributions to this section"
    )
    synthesized_content: str = Field(
        default="", 
        description="Combined/synthesized content from all agent contributions"
    )
    synthesis_method: str = Field(
        default="smart_merge", 
        description="Method used to synthesize content: smart_merge, concatenate, primary_only"
    )
    
    # Legacy support - kept for backwards compatibility
    content: Optional[str] = Field(
        default=None, 
        description="Legacy single content field (deprecated, use synthesized_content)"
    )
    
    status: str = Field(default="draft", description="Section status: draft, completed, needs_revision")
    agent_contributors: List[str] = Field(default_factory=list, description="List of agent names that contributed")
    last_updated: Optional[datetime] = Field(default=None, description="Last update timestamp")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Quality metrics for the section")


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
    enable_verification: bool = Field(default=True, description="Enable fact verification for report sections")
    use_parallel_processing: bool = Field(default=True, description="Enable parallel section generation")
    custom_llm_map: Dict[str, str] = Field(default_factory=dict, description="Override LLM provider for specific sections, e.g. {'Trends': 'perplexity'}")


class ReportResponse(BaseModel):
    success: bool
    message: str
    report_id: Optional[str] = None
    report: Optional[ReportModel] = None


class SectionUpdateRequest(BaseModel):
    section_id: str = Field(..., description="Section ID to update")
    feedback: str = Field(..., description="Feedback for section improvement")
    user_id: str = Field(..., description="User ID")
