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

import asyncio
import time
from typing import List
from .engineer import EngineerAgent
from .sales import SalesAgent
from .customer_connect import CustomerConnect
from .doc_master import DocMaster
from .pro_mentor import ProMentor
from .rival_watcher import RivalWatcher
from .tech_wiz import TechWiz
from .trend_tracker import TrendTracker
from config.manager import callModel
from schema.master_schema import AgentModel
from schema.cal_master_agent import json_schema, pydantic_schema
from config.agent_list import AgentDescriptions, master_agent_description_prompt


class MasterAgent:
    def create_prompt(prompt: str):
        schema_to_use = json_schema.json_schema
        agent_model = AgentModel(
            role=master_agent_description_prompt,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.MASTER_AGENT.value,
        )
        return agent_model

    async def agent_queue(tasks: List[pydantic_schema.AgentTask], provider: str):
        start = time.time()

        def process_task(task):
            if task.agent_name == AgentDescriptions.CUSTOMER_CONNECT.name:
                response = CustomerConnect.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.DOC_MASTER.name:
                response = DocMaster.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.ENGINEER_AGENT.name:
                response = EngineerAgent.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.PRO_MENTOR.name:
                response = ProMentor.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.RIVAL_WATCHER.name:
                response = RivalWatcher.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.SALES_AGENT.name:
                response = SalesAgent.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.TECH_WIZ.name:
                response = TechWiz.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.TREND_TRACKER.name:
                response = TrendTracker.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            else:
                response = None
            return response  # Return the response

        responses = [process_task(task) for task in tasks]

        # Now gather the calls to callModel
        await asyncio.gather(
            *(
                callModel(agent=response, provider=provider)
                for response in responses
                if response
            )
        )
        end = time.time()
        time_length = end - start
        print(f"It took {time_length} seconds")
