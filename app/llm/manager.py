import asyncio

from ..storage.firestore_db import store_agent_response, logger
from ..schema.master_schema import AgentModel, DatabaseModel, Provider
from ..config.config import GoogleClient, OpenAIClient


async def callModel(provider: Provider, model: int, agent: AgentModel): # Use Provider enum for type hinting
    try:
        if provider == Provider.GOOGLE:  # Check against enum members
            google_client = GoogleClient()  # Instantiate client *inside* the loop
            agent_call = await asyncio.to_thread(google_client.predict, agent=agent, model=model)
        elif provider == Provider.OPENAI:  # Check against enum members
            openai_client = OpenAIClient()  # Instantiate client *inside* the loop
            agent_call = await asyncio.to_thread(openai_client.predict, agent=agent, model=model)
        else:
            openai_client = OpenAIClient()  # Instantiate client *inside* the loop
            agent_call = await asyncio.to_thread(openai_client.predict, agent=agent, model=model)

        prepare_for_db = DatabaseModel(
            agent=agent.agent, content=agent_call, topic_id=agent.topic_id
        )
        await asyncio.to_thread(store_agent_response, prepare_for_db)
        return agent_call
    except Exception as e:
        logger.error(f"Error in callModel: {e}", exc_info=True)
        return {"error": str(e)}

