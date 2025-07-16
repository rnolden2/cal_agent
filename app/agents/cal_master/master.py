import asyncio
import time
from typing import List, Optional, Tuple
import logging
import orjson

from ...agent_schema.agent_master_schema import (
    AgentCallModel,
    AgentModel,
    DatabaseModel,
    Provider,
)
from .. import (
    CustomerConnect,
    EngineerAgent,
    RivalWatcher,
    SalesAgent,
    TechWiz,
    TrendTracker,
)
from ...config.agent_list import AgentDescriptions, master_agent_description_prompt
from ...llm.manager import callModel
from ...storage.firestore_db import set_topic_id
from .json_schema import json_schema_master
from .pydantic_schema import AgentTask
from ..aggregator.aggregator import Aggregator
from ...storage.firestore_db import store_agent_response

# Configure logging as needed
logging.basicConfig(level=logging.INFO)

class MasterAgent:
    @staticmethod
    def create_prompt(prompt: str) -> AgentModel:
        """
        Creates a master agent prompt using a predefined schema and description.
        """
        return AgentModel(
            role=master_agent_description_prompt,
            content=prompt,
            agent_schema=json_schema_master,
            agent=AgentDescriptions.MASTER_AGENT.name,
        )

    @staticmethod
    async def get_agent_tasks(
        agent_data: AgentModel, topic_id: str, user_id: str
    ) -> List[AgentTask]:
        """
        Calls the model to retrieve agent tasks based on the provided agent_data.
        """
        try:
            agent_data.topic_id = set_topic_id(topic_id)
            agent_data.user_id = user_id
            agent_data.provider = Provider.GOOGLE
            agent_data.model = 1

            master_agent_call = await callModel(agent=agent_data)
            response_dict = orjson.loads(master_agent_call)
            tasks_data = response_dict.get("response", {}).get("tasks", [])
            return [AgentTask(**task) for task in tasks_data]
        except Exception as e:
            logging.error(f"Error in get_agent_tasks: {e}", exc_info=True)
            return []

    @staticmethod
    def process_task(task: AgentTask) -> Optional[AgentModel]:
        """
        Processes a single task by creating an appropriate prompt for the agent.
        """
        prompt_with_context = f"{task.prompt} {task.additional_context}"
        agent_factories = {
            AgentDescriptions.CUSTOMER_CONNECT.name: CustomerConnect.create_prompt,
            AgentDescriptions.ENGINEER_AGENT.name: EngineerAgent.create_prompt,
            AgentDescriptions.RIVAL_WATCHER.name: RivalWatcher.create_prompt,
            AgentDescriptions.SALES_AGENT.name: SalesAgent.create_prompt,
            AgentDescriptions.TECH_WIZ.name: TechWiz.create_prompt,
            AgentDescriptions.TREND_TRACKER.name: TrendTracker.create_prompt,
        }
        create_func = agent_factories.get(task.agent_name)
        if create_func:
            return create_func(prompt_with_context)
        logging.warning(f"No processing function defined for agent: {task.agent_name}")
        return None

    @staticmethod
    async def store_agent_response_in_db(
        agent_call: AgentCallModel, responses: List[str]
    ) -> None:
        """
        Stores agent responses in the database along with their agent names.
        """
        try:
            tasks_for_db: List[DatabaseModel] = [
                DatabaseModel(
                    content=response,
                    topic_id=agent_call.topic_id,
                    user_id=agent_call.user_id,
                    agent_name=orjson.loads(response)["agent"],  # Make sure your DatabaseModel supports this field.
                )
                for  response in responses
            ]
            await asyncio.gather(
                *(store_agent_response(response=db_item) for db_item in tasks_for_db)
            )
            logging.info("Agent responses stored in the database successfully.")
        except Exception as e:
            logging.error(f"Error in store_agent_response_in_db: {e}", exc_info=True)


    @staticmethod
    async def orchestrate_tasks(agent_call: AgentCallModel) -> str:
        """
        Orchestrates the tasks by creating the master prompt, retrieving tasks,
        processing them, and then scheduling downstream processing.
        """
        start_time = time.time()
        prompt = agent_call.response
        topic_id = agent_call.topic_id
        user_id = agent_call.user_id

        master_prompt = MasterAgent.create_prompt(prompt)
        tasks: List[AgentTask] = await MasterAgent.get_agent_tasks(master_prompt, topic_id, user_id)
        processed_agents: List[AgentModel] = [
            MasterAgent.process_task(task) for task in tasks if task
        ]

        async def process_agent_responses():
            try:
                # Gather responses along with agent names.
                agent_response: List[str] = await asyncio.gather(
                    *(
                        callModel(agent_model)
                        for agent_model in processed_agents if agent_model is not None
                    )
                )

                promentor_response = await Aggregator.call_pro_mentor(Aggregator.aggregate_responses([response for response in agent_response]))
                agent_response.append(promentor_response)
                print(f"Agent Responses: {agent_response}")

                await MasterAgent.store_agent_response_in_db(agent_call, agent_response)
            except Exception as e:
                logging.error(f"Error in processing agent responses: {e}", exc_info=True)

        # Schedule background processing and return immediately.
        asyncio.create_task(process_agent_responses())
        elapsed = time.time() - start_time
        logging.info(f"Orchestration triggered in {elapsed:.2f} seconds")
        return "Completed"