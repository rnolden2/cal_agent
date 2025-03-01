import asyncio
import logging
from typing import List
from .json_schema import json_schema_reviewer
from ...agents import ProMentor
from ...agent_schema.agent_master_schema import AgentModel
from ...llm.manager import callModel
from ...config.agent_list import AgentDescriptions

class Aggregator:
    def __init__(self):
        pass

    @staticmethod
    def aggregate_responses(responses: List[str]) -> str:
        """
        Aggregates the responses from the agents into a single response.
        """
        return " ".join(responses)

    @staticmethod
    async def call_pro_mentor(joined_response: str):
        """
        Calls the ProMentor agent with the joined response.
        """
        prompt = (
            "Using the following information, provide personal and professional development advice: "
            + joined_response
        )
        agent_model: AgentModel = ProMentor.create_prompt(prompt)
        agent_response = await callModel(agent=agent_model)
        print(f"ProMentor response: {agent_response}")
        return agent_response

    @staticmethod
    async def process_aggregated_responses(responses: List[str]) -> List[str]:
        """
        Processes the aggregated responses from the agents.
        """
        joined_response = Aggregator.aggregate_responses(responses)
        pro_mentor_response = await Aggregator.call_pro_mentor(joined_response)
        joined_response += pro_mentor_response
        reviewed_responses: List[str] = Aggregator.review_responses(joined_response)
        return reviewed_responses

    @staticmethod
    async def review_responses(responses: List[str]) -> List[str]:
        """
        Reviews the responses from the agents to ensure correct format for database write.
        """
        # Create an AgentModel for each response string
        new_response_list: List[AgentModel] = [
            AgentModel(
                agent=AgentDescriptions.REVIEWER.name,
                agent_schema = json_schema_reviewer,
                role=AgentDescriptions.REVIEWER.value,
                content=response,
            )
            for response in responses
        ]

        try:
            # Process all agent models concurrently
            reviewed_responses: List[str] = await asyncio.gather(
                *(callModel(agent=agent_model) for agent_model in new_response_list)
            )
            # Combine the reviewed responses (adjust the joiner as needed)
            return reviewed_responses
        except Exception as e:
            logging.error(f"Error in processing agent responses: {e}")
            return None
        
