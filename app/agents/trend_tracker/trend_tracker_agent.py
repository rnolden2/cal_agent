"""
The Trend Tracker Agent continuously monitors the web for the latest 
trends and developments in military vehicle hybridization and electrification. 
It stays updated with solicitations from agencies like SBIR, DoD, DoE, and 
NAMC related to permanent magnet motors/generators, power conversion, and 
inverters. Additionally, it tracks announcements of relevant programs and awards.
"""
from schema.master_schema import AgentModel
from .json_schema import json_schema
from config.agent_list import AgentDescriptions

class TrendTracker():
    def create_prompt(prompt:str):
        schema_to_use = json_schema.json_schema
        agent_model = AgentModel(role=AgentDescriptions.TREND_TRACKER.value,content=prompt,agent_schema=schema_to_use, agent=AgentDescriptions.TREND_TRACKER.name)
        return agent_model
    
