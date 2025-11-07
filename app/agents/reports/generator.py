
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


async def combine_reports(aggregated_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges reports from multiple providers into a single JSON report.

    Args:
        aggregated_report: A dictionary containing the reports from all providers.

    Returns:
        A dictionary containing the merged report.
    """

    combined = {
        "title": f"Combined Report for {aggregated_report['topic']}",
        "executiveSummary": "",
        "sections": [],
        "recommendations": [],
        "conclusion": "",
        "metadata": {"sources": [], "date": ""}
    }

    sections_dict = {}
    all_recommendations = []
    all_sources = set()

    for report in aggregated_report["reports"]:
        provider = report['provider']
        rep = report['response']

        combined["executiveSummary"] += f"\n\nFrom {provider}: {rep.get('executiveSummary', '')}"

        for sec in rep.get('sections', []):
            title = sec['sectionTitle']
            if title not in sections_dict:
                sections_dict[title] = {
                    "sectionTitle": title,
                    "content": "",
                    "subsections": []
                }
            sections_dict[title]["content"] += f"\n\nFrom {provider}: {sec['content']}"
            sections_dict[title]["subsections"].extend(sec.get('subsections', []))

        all_recommendations.extend(rep.get('recommendations', []))

        combined["conclusion"] += f"\n\nFrom {provider}: {rep.get('conclusion', '')}"

        all_sources.update(rep.get('metadata', {}).get('sources', []))

    combined["sections"] = list(sections_dict.values())
    combined["recommendations"] = all_recommendations
    combined["metadata"]["sources"] = list(all_sources)
    # Set date to current or leave as is

    return combined


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

        schema_str = json.dumps(json_schema_report)
        prompt = f"{template}\n\nTopic: {research_request.topic}\n\nOutput your response strictly as JSON conforming to this schema: {schema_str}"
        agent_data: AgentModel = GeneralAgent.create_prompt(prompt)
        agent_data.provider = provider
        agent_data.model = 1

        response = await callModel(agent=agent_data)
        response_data = orjson.loads(response)
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

    combined_report = await combine_reports(aggregated_report)
    aggregated_report["combined_report"] = combined_report


    return aggregated_report
