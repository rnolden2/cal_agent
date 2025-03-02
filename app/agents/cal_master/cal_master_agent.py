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

import orjson
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
from .additional_context import additional_context, feedback_notes
from .pydantic_schema import AgentTask
from ...llm.manager import callModel
from ...agent_schema.agent_master_schema import AgentModel, Provider
from ...config.agent_list import AgentDescriptions, master_agent_description_prompt
from .json_schema import json_schema_master


class MasterAgent:


    def create_prompt(prompt: str) -> AgentModel:
        json_schema_related_data = {
            "type": "object",
            "properties": {
                "related_data": {
                    "type": "string",
                    "description": "The context provided by the user.",
                },
                "required": [
                    "related_data",
                ],
                "description": "Schema for getting related data.",
            },
        }        
        related_data_prompt = (
            "Using this prompt pull all related data useful to support the response. prompt: "
            + prompt
            + " Data: "
            + additional_context
        )
        schema_to_use = json_schema_master
        # related_data_response = AgentModel(
        #     role="Organizer",
        #     content=related_data_prompt,
        #     agent_schema=json_schema_related_data,
        #     agent="Organizer",
        # )
        # related_data_call = await callModel(
        #     agent=related_data_response,
        #     provider="google",
        #     model=0,
        # )
        # response_dict = orjson.loads(related_data_call)
        agent_model = AgentModel(
            role=master_agent_description_prompt,
            content=prompt,
            additional_context="",
            agent_schema=schema_to_use,
            agent=AgentDescriptions.MASTER_AGENT.name,
        )
        return agent_model

    async def agent_queue(
        tasks: List[AgentTask],
        provider: Provider,
        model: int,
        topic_id: str,
        user_id: str,
    ):
        start = time.time()

        def process_task(task: AgentTask, topic_id: str):
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
                response = ProMentor.create_prompt(task.prompt + " " + feedback_notes)
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

            if response and topic_id and user_id:
                response.topic_id = topic_id
                response.user_id = user_id
            return response  # Return the response

        responses = [process_task(task, topic_id=topic_id) for task in tasks]

        # Gather the calls to callModel
        agent_responses = await asyncio.gather(
            *(
                callModel(
                    agent=response,
                    provider=provider,
                    model=model,
                )
                for response in responses
                if response
            )
        )

        # Use all agent responses to use when invoking the Professional Mentor Agent
        # combined_response = "\n\n".join(agent_responses)

        end = time.time()
        time_length = end - start
        print(f"It took {time_length} seconds")
        return "Completed"
