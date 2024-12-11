"""
The Sales Agent is an expert in government and defense sales strategies, 
combining traditional business sales methods with modern approaches. It 
provides actionable recommendations to optimize sales processes and maximize 
business opportunities. This agent identifies key decision-makers, suggests 
engagement tactics, and highlights follow-up strategies to improve client 
relationships. It also analyzes market trends to uncover untapped opportunities, 
ensuring the business stays ahead in competitive government and defense sectors.
"""
from schema.master_schema import AgentModel
from .json_schema import json_schema
from config.agent_list import AgentDescriptions

class SalesAgent():
    def create_prompt(prompt:str):
        schema_to_use = json_schema
        agent_model = AgentModel(role=AgentDescriptions.SALES.value,content=prompt,agent_schema=schema_to_use, agent=AgentDescriptions.SALES.name)
        return agent_model
    
