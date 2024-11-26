from pydantic import BaseModel, Field
from typing import List, Dict, Union, Optional

class AgentTask(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to handle the task.")
    prompt: str = Field(..., description="Task-specific prompt crafted for the agent.")
    additional_context: str = Field(
        None, description="Optional additional context for the task."
    )

class MasterAgent(BaseModel):
    content: str = Field(..., description="The content or context provided by the user.")
    timestamp: int = Field(..., description="The timestamp in milliseconds when the input was generated.")
    task_description: str = Field(..., description="Summary of tasks derived from context.")
    agents_involved: List[str] = Field(..., description="List of agent names involved in the task. Agents are")
    tasks: List[AgentTask] = Field(..., description="Tasks routed to individual agents.")

