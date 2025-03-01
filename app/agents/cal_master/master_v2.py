import asyncio
import time
from typing import List, Optional
import logging
import orjson

from ...agent_schema.agent_master_schema import (
    AgentCallModel,
    AgentModel,
    DatabaseModel,
    Provider,
)
from ...agents import (
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
        schema_to_use = json_schema_master
        return AgentModel(
            role=master_agent_description_prompt,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.MASTER_AGENT.name,
        )

    @staticmethod
    async def get_agent_tasks(
        agent_data: AgentModel, topic_id: str, user_id: str
    ) -> List[AgentTask]:
        """
        Makes a call to the model to retrieve agent tasks based on the provided agent_data.
        """
        try:
            agent_data.topic_id = set_topic_id(topic_id)
            agent_data.user_id = user_id
            agent_data.provider = Provider.GOOGLE
            agent_data.model = 1

            master_agent_call = await callModel(agent=agent_data)
            response_dict = orjson.loads(master_agent_call)
            tasks_data = response_dict["response"]["tasks"]
            return [AgentTask(**task) for task in tasks_data]
        except Exception as e:
            logging.error(f"Error in get_agent_tasks: {e}")
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
        else:
            logging.warning(
                f"No processing function defined for agent: {task.agent_name}"
            )
            return None

    @staticmethod
    async def orchestrate_tasks(agent_call: AgentCallModel) -> str:
        """
        Orchestrates the tasks by creating the master prompt, retrieving tasks, processing them, and
        calling the model for each processed task.
        """
        start_time = time.time()
        prompt = agent_call.response
        topic_id = agent_call.topic_id
        user_id = agent_call.user_id

        # Create the master agent prompt.
        agent_model = MasterAgent.create_prompt(prompt)

        # Retrieve tasks from the model.
        tasks: List[AgentTask] = await MasterAgent.get_agent_tasks(
            agent_model, topic_id, user_id
        )

        # Process each task into an AgentModel.
        responses: List[AgentModel] = [
            MasterAgent.process_task(task) for task in tasks if task
        ]

        async def process_agent_responses(agent_call: AgentCallModel):
            try:
                # Asynchronously call the model for each processed task.
                agent_responses: List[str] = await asyncio.gather(
                    *(
                        callModel(agent=agent_task)
                        for agent_task in responses
                        if agent_task is not None
                    )
                )
                # Once all responses are gathered, trigger Reviewer agent and database write.
                aggregated_responses: List[
                    str
                ] = await Aggregator.process_aggregated_responses(agent_responses)
                await asyncio.create_task(
                    store_agent_response(agent_call, aggregated_responses)
                )
            except Exception as e:
                logging.error(f"Error in processing agent responses: {e}")

        # Schedule the background task; we do not await it here.
        asyncio.create_task(process_agent_responses(agent_call))

        elapsed = time.time() - start_time
        logging.info(f"Orchestration triggered in {elapsed:.2f} seconds")
        return "Completed"

    async def store_agent_response_in_db(
        agent_call: AgentCallModel, responses: List[str]
    ):
        try:
            prepare_for_db_list: List[DatabaseModel] = [
                DatabaseModel(
                    content=response,
                    topic_id=agent_call.topic_id,
                    user_id=agent_call.user_id,
                )
                for response in responses
            ]

            await asyncio.gather(
                *(
                    store_agent_response(response=response)
                    for response in prepare_for_db_list
                )
            )
            logging.info("Success: Agent responses stored in database.")
        except Exception as e:
            logging.error(f"Error in store_agent_response_in_db: {e}", exc_info=True)
