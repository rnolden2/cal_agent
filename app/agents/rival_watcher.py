"""
The Rival Watcher Agent keeps an up-to-date repository of 
competitor information. It gathers useful details on competitors' new 
developments, locations, divisions or departments, and points of contact.
"""
from schema.master_schema import AgentModel
from schema.rival_watcher import json_schema, pydantic_schema
from config.agent_list import AgentDescriptions

class RivalWatcher():
    def create_prompt(prompt:str, provider:int):
        schema_to_use = json_schema.json_schema if provider == 0 else pydantic_schema.InputContext
        agent_model = AgentModel(role=AgentDescriptions.RIVAL_WATCHER.value,content=prompt,agent_schema=schema_to_use)
        return agent_model
    
