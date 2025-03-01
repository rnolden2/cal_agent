import asyncio
from typing import Dict

from ..storage.firestore_db import store_agent_response, logger
from ..agent_schema.agent_master_schema import AgentModel, DatabaseModel, Provider
from ..config.config import GoogleClient, OpenAIClient, PerplexityClient


async def callModel(agent: AgentModel) -> str:
    try:
        provider_clients: Dict[Provider, type] = {  # Type hint added for clarity
            Provider.GOOGLE: GoogleClient,
            Provider.OPENAI: OpenAIClient,
            Provider.PERPLEXITY: PerplexityClient,
        }

        client_class = provider_clients.get(agent.provider) or OpenAIClient
        client = client_class()  # Instantiate the client

        if agent.provider == Provider.PERPLEXITY:
            agent_call = await client.predict(agent=agent)
        else:
            agent_call = await asyncio.to_thread(client.predict, agent=agent)

        return agent_call
    except Exception as e:
        logger.error(f"Error in callModel: {e}", exc_info=True)
        return {"error": str(e)}

    
