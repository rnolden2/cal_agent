"""
The Technical Wizard Agent assists in creating all necessary technical 
content. This includes bullet points for presentations, sections for 
proposals, technical responses, and clear explanations of complex topics.
"""
from schema.master_schema import AgentModel
from schema.tech_wiz import json_schema, pydantic_schema
from config.agent_list import AgentDescriptions

class TechWiz():
    def create_prompt(prompt:str, provider:int):
        schema_to_use = json_schema.json_schema if provider == 0 else pydantic_schema.InputContext
        agent_model = AgentModel(role=AgentDescriptions.TECH_WIZ.value,content=prompt,agent_schema=schema_to_use)
        return agent_model
    
