"""
The Rival Watcher Agent keeps an up-to-date repository of 
competitor information. It gathers useful details on competitors' new 
developments, locations, divisions or departments, and points of contact.
"""
from ...agent_schema.agent_master_schema import AgentModel
from .json_schema import json_schema_rival_watcher
from ...config.agent_list import AgentDescriptions

class RivalWatcher:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_rival_watcher
        agent_model = AgentModel(
            role=AgentDescriptions.RIVAL_WATCHER.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.RIVAL_WATCHER.name,
        )
        return agent_model

