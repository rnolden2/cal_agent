import asyncio
from typing import Dict

from ..storage.firestore_db import store_agent_response, logger
from ..agent_schema.agent_master_schema import AgentModel, DatabaseModel, Provider
from ..config.config import GoogleClient, OpenAIClient, PerplexityClient


async def callModel(provider: Provider, model: int, agent: AgentModel):
    try:
        provider_clients: Dict[Provider, type] = {  # Type hint added for clarity
            Provider.GOOGLE: GoogleClient,
            Provider.OPENAI: OpenAIClient,
            Provider.PERPLEXITY: PerplexityClient,
        }

        client_class = provider_clients.get(provider) or OpenAIClient
        client = client_class()  # Instantiate the client

        if provider == Provider.PERPLEXITY:
            agent_call = await client.predict(agent=agent, model=model)
        else:
            agent_call = await asyncio.to_thread(client.predict, agent=agent, model=model)

        prepare_for_db = DatabaseModel(
            agent=agent.agent,
            content=agent_call,
            topic_id=agent.topic_id,
            user_id=agent.user_id,
        )
        await asyncio.to_thread(store_agent_response, prepare_for_db)
        return agent_call
    except Exception as e:
        logger.error(f"Error in callModel: {e}", exc_info=True)
        return {"error": str(e)}
