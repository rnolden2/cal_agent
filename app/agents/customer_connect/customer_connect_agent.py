"""
The Customer Connect Agent assists in crafting professional email 
responses and drafts for customers. It offers suggestions on whom to 
contact, optimal follow-up timings, and advises on information sharing, 
especially when an NDA is not in place.
"""
from ...agent_schema.agent_master_schema import AgentModel
from ...config.agent_list import AgentDescriptions
from ...agents.customer_connect.json_schema import json_schema_customer_connect

class CustomerConnect:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_customer_connect
        agent_model = AgentModel(
            role=AgentDescriptions.CUSTOMER_CONNECT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.CUSTOMER_CONNECT.name,
        )
        return agent_model
