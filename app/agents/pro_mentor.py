"""
The Professional Mentor Agent provides coaching to enhance work performance, 
increase value, and improve efficiency. It suggests optimal timing for tasks, 
recommends additional initiatives to exceed expectations, and incorporates past 
feedback to refine future guidance.
"""
from schema.master_schema import AgentModel
from schema.pro_mentor import json_schema, pydantic_schema
from config.agent_list import AgentDescriptions

class ProMentor():
    def create_prompt(prompt:str):
        schema_to_use = json_schema.json_schema
        agent_model = AgentModel(role=AgentDescriptions.PRO_MENTOR.value,content=prompt,agent_schema=schema_to_use,agent=AgentDescriptions.PRO_MENTOR.name)
        return agent_model
    
