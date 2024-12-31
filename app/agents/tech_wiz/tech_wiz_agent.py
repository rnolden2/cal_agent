"""
The Technical Wizard Agent assists in creating all necessary technical 
content. This includes bullet points for presentations, sections for 
proposals, technical responses, and clear explanations of complex topics.
"""
from ...agent_schema.agent_master_schema import AgentModel
from ...config.agent_list import AgentDescriptions
from .json_schema import json_schema_tech_wiz

class TechWiz:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_tech_wiz
        agent_model = AgentModel(
            role=AgentDescriptions.TECH_WIZ.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.TECH_WIZ.name,
        )
        return agent_model
