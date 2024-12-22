"""
The Engineer Agent is a strategic thinker that focuses on enhancing 
understanding of engineering fundamentals and big-picture concepts. 
It provides insights into technical terms, equations, and best practices 
relevant to a given task. This agent connects tasks to broader engineering 
principles, offering recommendations to improve technical knowledge and 
problem-solving. It suggests resources such as textbooks, research papers, 
and online courses to deepen understanding and ensure technical excellence.
"""
from ...schema.master_schema import AgentModel
from ...config.agent_list import AgentDescriptions
from .json_schema import json_schema as json_schema_engineer

class EngineerAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_engineer
        agent_model = AgentModel(
            role=AgentDescriptions.ENGINEER_AGENT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.ENGINEER_AGENT.name,
        )
        return agent_model

