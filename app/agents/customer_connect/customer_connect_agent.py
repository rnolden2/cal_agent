"""
The Customer Connect Agent assists in crafting professional email 
responses and drafts for customers. It offers suggestions on whom to 
contact, optimal follow-up timings, and advises on information sharing, 
especially when an NDA is not in place.
"""
from schema.master_schema import AgentModel
from .json_schema import json_schema
from config.agent_list import AgentDescriptions

class CustomerConnect():
    def create_prompt(prompt:str):
        schema_to_use = json_schema
        agent_model = AgentModel(role=AgentDescriptions.CUSTOMER_CONNECT.value,content=prompt,agent_schema=schema_to_use, agent=AgentDescriptions.CUSTOMER_CONNECT.name)
        return agent_model
    
