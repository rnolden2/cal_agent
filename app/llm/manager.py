import asyncio
import logging
from typing import Dict

from ..agent_schema.agent_master_schema import AgentModel, DatabaseModel, Provider
from ..config.config import GoogleClient, OpenAIClient, PerplexityClient
from ..utils.llm_counter import increment_llm_call_counter


async def callModel(agent: AgentModel) -> str:
    try:
        increment_llm_call_counter()  # Increment the counter for each call
        provider_clients: Dict[Provider, type] = {
            Provider.GOOGLE: GoogleClient,
            Provider.OPENAI: OpenAIClient,
            Provider.PERPLEXITY: PerplexityClient,
        }
        client_class = provider_clients.get(agent.provider) or GoogleClient
        client = client_class()  # Instantiate the client
        if agent.provider == Provider.PERPLEXITY:
            return await client.predict(agent=agent)
        # Offload blocking calls to a thread.
        return await asyncio.to_thread(client.predict, agent=agent)
    except Exception as e:
        logging.error(f"Error in callModel: {e}", exc_info=True)
        return f"Error: {e}"
