"""
The Sales Agent is an expert in government and defense sales strategies, 
combining traditional business sales methods with modern approaches. It 
provides actionable recommendations to optimize sales processes and maximize 
business opportunities. This agent identifies key decision-makers, suggests 
engagement tactics, and highlights follow-up strategies to improve client 
relationships. It also analyzes market trends to uncover untapped opportunities, 
ensuring the business stays ahead in competitive government and defense sectors.
"""
from ...agent_schema.agent_master_schema import AgentModel
from ...config.agent_list import AgentDescriptions
from .json_schema import json_schema_sales_agent

class SalesAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_sales_agent
        agent_model = AgentModel(
            role=AgentDescriptions.SALES_AGENT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.SALES_AGENT.name,
        )
        return agent_model


