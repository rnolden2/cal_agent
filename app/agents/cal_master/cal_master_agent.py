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
from ...agents import (
    CustomerConnect,
    DocMaster,
    EditorAgent,
    EngineerAgent,
    ProMentor,
    SalesAgent,
    RivalWatcher,
    TechWiz,
    TrendTracker,
)
from .pydantic_schema import AgentTask
from ...llm.manager import callModel
from ...schema.master_schema import AgentModel
from ...config.agent_list import AgentDescriptions, master_agent_description_prompt
from .json_schema import json_schema as json_schema_master


class MasterAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_master
        agent_model = AgentModel(
            role=master_agent_description_prompt,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.MASTER_AGENT.name,
        )
        return agent_model

    async def agent_queue(tasks: List[AgentTask], provider: str, topic_id: str = None):
        start = time.time()

        def process_task(task: AgentTask, topic_id: str = None):
            if task.agent_name == AgentDescriptions.CUSTOMER_CONNECT.name:
                response: AgentModel = CustomerConnect.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.DOC_MASTER.name:
                response = DocMaster.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.EDITOR_AGENT.name:
                response = EditorAgent.create_prompt(
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

            if response and topic_id:
                response.topic_id = topic_id
            return response  # Return the response

        responses = [process_task(task, topic_id=topic_id) for task in tasks]

        # Now gather the calls to callModel
        agent_responses = await asyncio.gather(
            *(
                callModel(agent=response, provider=provider)
                for response in responses
                if response
            )
        )

        # Use all agent responses to use when invoking the Professional Mentor Agent
        combined_response = "\n\n".join(agent_responses)
        # try:
        #     pro_mentor_prompt = ProMentor.create_prompt(combined_response)
        #     await callModel(agent=pro_mentor_prompt, provider=provider)
        # except Exception as e:
        #     print(f"Error calling ProMentor agent: {e}")

        end = time.time()
        time_length = end - start
        print(f"It took {time_length} seconds")
        return combined_response
