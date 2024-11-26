"""
The Document Master Agent manages and retrieves stored documents, 
such as military standards, technical papers, presentations, and other 
relevant materials, facilitating quick access when needed.
"""
from schema.master_schema import AgentModel
from schema.doc_master import json_schema, pydantic_schema
from config.agent_list import AgentDescriptions


class DocMaster():
    def create_prompt(prompt:str, provider:int):
        schema_to_use = json_schema.json_schema if provider == 0 else pydantic_schema.InputContext
        agent_model = AgentModel(role=AgentDescriptions.DOC_MASTER.value,content=prompt,agent_schema=schema_to_use)
        return agent_model
    
