
import asyncio
import orjson
from typing import Dict, Any

from ...agent_schema.agent_master_schema import AgentModel, Provider
from ...agents.general.general_agent import GeneralAgent
from ...llm.manager import callModel
from ...models.model_list import (
    google_models,
    openai_models,
    perplexity_models,
)

async def combine_reports(aggregated_report: Dict[str, Any]) -> str:
    """
    Combines reports from multiple providers into a single report using OpenAI.

    Args:
        aggregated_report: A dictionary containing the reports from all providers.

    Returns:
        A string containing the combined report.
    """
    prompt = "Please synthesize the following reports into a single, comprehensive report:\n\n"
    for report in aggregated_report["reports"]:
        prompt += f"Provider: {report['provider']}\n"
        prompt += f"Report: {report['response']}\n\n"

    agent_data: AgentModel = GeneralAgent.create_prompt(prompt)
    agent_data.provider = Provider.OPENAI
    agent_data.model = 1  # Use a powerful model for synthesis

    combined_report = await callModel(agent=agent_data)
    return combined_report


async def generate_report_from_all_providers(
    research_request: AgentModel, template: str
) -> Dict[str, Any]:
    """
    Generates a market research report by querying the General agent
    across all available providers (Google, OpenAI, Perplexity) and
    aggregates their responses.

    Args:
        research_request: The request object containing the research topic.
        template: The template to be used for generating the report.

    Returns:
        A dictionary containing the aggregated report from all providers.
    """
    providers = [
        (Provider.GOOGLE, google_models[1] if google_models else None),
        (Provider.OPENAI, openai_models[1] if openai_models else None),
        (
            Provider.PERPLEXITY,
            perplexity_models[0] if perplexity_models else None,
        ),
    ]

    async def query_provider(provider, model_name):
        if not model_name:
            return {
                "provider": provider.value,
                "response": "No model configured for this provider.",
            }

        prompt = f"{template}\n\nTopic: {research_request.topic}"
        agent_data: AgentModel = GeneralAgent.create_prompt(prompt)
        agent_data.provider = provider
        agent_data.model = 1

        response = await callModel(agent=agent_data)
        try:
            # Perplexity returns a JSON string, others might return text.
            response_data = orjson.loads(response)
        except orjson.JSONDecodeError:
            response_data = {"content": response}

        return {"provider": provider.value, "response": response_data}

    tasks = [
        query_provider(provider, model)
        for provider, model in providers
        if model
    ]
    results = await asyncio.gather(*tasks)

    aggregated_report = {"topic": research_request.topic, "reports": []}
    for result in results:
        aggregated_report["reports"].append(result)

    combined_report_str = await combine_reports(aggregated_report)
    try:
        combined_report_json = orjson.loads(combined_report_str)
        aggregated_report["combined_report"] = combined_report_json
    except orjson.JSONDecodeError:
        aggregated_report["combined_report"] = {"content": combined_report_str}


    return aggregated_report
