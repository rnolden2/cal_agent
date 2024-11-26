"""
The Master Agent acts as the orchestrator, ensuring requests 
are routed to the appropriate agents based on the task's requirements. 
It manages interactions between the user and multiple specialized agents, 
aggregates responses when necessary, and provides a unified interface 
for seamless communication. With the ability to intelligently direct 
tasks, the Manager Agent optimizes workflows, handles multi-agent 
responses, and enhances user efficiency. It is designed to be adaptable 
and scalable, making it a vital component for coordinating complex 
operations across agents.
"""

from schema.master_schema import AgentModel
from schema.cal_master_agent import json_schema, pydantic_schema
from config.agent_list import master_agent_description_prompt

class MasterAgent():
    def create_prompt(prompt:str, provider:int):
        schema_to_use = json_schema.json_schema #if provider == 0 else pydantic_schema.MasterAgent
        agent_model = AgentModel(role=master_agent_description_prompt,content=prompt,agent_schema=schema_to_use, )
        return agent_model