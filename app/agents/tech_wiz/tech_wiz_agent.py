"""
The Technical Wizard Agent assists in creating all necessary technical 
content. This includes bullet points for presentations, sections for 
proposals, technical responses, and clear explanations of complex topics.
"""
from schema.master_schema import AgentModel
from .json_schema import json_schema
from config.agent_list import AgentDescriptions

class TechWiz():
    def create_prompt(prompt:str):
        schema_to_use = json_schema
        agent_model = AgentModel(role=AgentDescriptions.TECH_WIZ.value,content=prompt,agent_schema=schema_to_use, agent=AgentDescriptions.TECH_WIZ.name)
        return agent_model
    
