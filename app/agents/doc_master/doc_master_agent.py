"""
The Document Master Agent manages and retrieves stored documents, 
such as military standards, technical papers, presentations, and other 
relevant materials, facilitating quick access when needed.
"""
from schema.master_schema import AgentModel
from .json_schema import json_schema
from config.agent_list import AgentDescriptions


class DocMaster():
    def create_prompt(prompt:str):
        schema_to_use = json_schema
        agent_model = AgentModel(role=AgentDescriptions.DOC_MASTER.value,content=prompt,agent_schema=schema_to_use, agent=AgentDescriptions.DOC_MASTER.name)
        return agent_model
    
