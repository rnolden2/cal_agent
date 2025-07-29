import logging
from typing import List
from ...agents import ProMentor
from ...agent_schema.agent_master_schema import  AgentModel
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
            "Additional information for reference: "
            + joined_response
        )
        # Import ProMentor locally to avoid potential circular imports.
        pro_mentor_model: AgentModel = ProMentor.create_prompt(prompt)
        agent_response = await callModel(agent=pro_mentor_model)
        logging.info(f"ProMentor response: {agent_response}")
        return agent_response

    