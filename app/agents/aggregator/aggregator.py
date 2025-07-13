import asyncio
import logging
from typing import List, Optional
from .json_schema import json_schema_reviewer
from ...agents import ProMentor
from ...agent_schema.agent_master_schema import AgentCallModel, AgentModel
from ...llm.manager import callModel
from ...config.agent_list import AgentDescriptions


class Aggregator:
    @staticmethod
    def aggregate_responses(responses: List[str]) -> str:
        """
        Aggregates the responses from the agents into a single response.
        """
        return " ".join(responses)

    @staticmethod
    async def call_pro_mentor(joined_response: str) -> str:
        """
        Calls the ProMentor agent with the aggregated response.
        """
        prompt = (
            "Using the following information, provide personal and professional development advice: "
            + joined_response
        )
        # Import ProMentor locally to avoid potential circular imports.
        pro_mentor_model: AgentModel = ProMentor.create_prompt(prompt)
        agent_response = await callModel(agent=pro_mentor_model)
        logging.info(f"ProMentor response: {agent_response}")
        return agent_response

    @staticmethod
    async def process_aggregated_responses(
        responses: List[str], agent_call: AgentCallModel
    ) -> List[str]:
        """
        Processes the aggregated responses from the agents.
        """
        joined_response = Aggregator.aggregate_responses(responses)
        pro_mentor_response = await Aggregator.call_pro_mentor(joined_response)
        joined_response += " " + pro_mentor_response
        # Pass the aggregated string as a single-element list for review.
        reviewed_responses = await Aggregator.review_responses([joined_response])
        return reviewed_responses if reviewed_responses is not None else []

    @staticmethod
    async def review_responses(responses: List[str]) -> Optional[List[str]]:
        """
        Reviews the responses from the agents to ensure they are in the correct format
        for writing to the database.
        """
        new_response_list: List[AgentModel] = [
            AgentModel(
                agent=AgentDescriptions.REVIEWER.name,
                agent_schema=json_schema_reviewer,
                role=AgentDescriptions.REVIEWER.value,
                content=response,
            )
            for response in responses
        ]
        try:
            reviewed: List[str] = await asyncio.gather(
                *(callModel(agent=agent_model) for agent_model in new_response_list)
            )
            return reviewed
        except Exception as e:
            logging.error(f"Error in review_responses: {e}", exc_info=True)
            return None