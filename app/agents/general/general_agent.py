"""
The General Agent is a versatile agent that can be used for any task
that doesn't fit into a more specialized agent's role. It takes a
prompt and returns a response from the language model.
"""
from ...agent_schema.agent_master_schema import AgentModel
from ...config.agent_list import AgentDescriptions
from .json_schema import json_schema_general

class GeneralAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_general
        agent_model = AgentModel(
            role=AgentDescriptions.GENERAL.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.GENERAL.name,
        )
        return agent_model
