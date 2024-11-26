"""
The Trend Tracker Agent continuously monitors the web for the latest 
trends and developments in military vehicle hybridization and electrification. 
It stays updated with solicitations from agencies like SBIR, DoD, DoE, and 
NAMC related to permanent magnet motors/generators, power conversion, and 
inverters. Additionally, it tracks announcements of relevant programs and awards.
"""
from schema.master_schema import AgentModel
from schema.trend_tracker import json_schema, pydantic_schema
from config.agent_list import AgentDescriptions

class TrendTracker():
    def create_prompt(prompt:str, provider:int):
        schema_to_use = json_schema.json_schema if provider == 0 else pydantic_schema.InputContext
        agent_model = AgentModel(role=AgentDescriptions.TREND_TRACKER.value,content=prompt,agent_schema=schema_to_use)
        return agent_model
    
