"""
The Editor Agent is a skilled editor that applies the principles from two 
renowned books—“The Elements of Style” by William Strunk Jr. and E.B. White 
and “On Writing Well” by William Zinsser—to refine technical writing. This 
agent ensures clarity, brevity, and professionalism in written content. It 
polishes grammar, tone, and structure, while providing a summary of applied 
changes and additional recommendations for improvement. The Editor Agent 
focuses on making technical content both precise and engaging for its 
intended audience.
"""
from ...schema.master_schema import AgentModel
from ...config.agent_list import AgentDescriptions
from .json_schema import json_schema as json_schema_editor

class EditorAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_editor
        agent_model = AgentModel(
            role=AgentDescriptions.EDITOR_AGENT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.EDITOR_AGENT.name,
        )
        return agent_model
