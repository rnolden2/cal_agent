import asyncio

from fastapi import logger

from ..storage.firestore_db import store_agent_response
from ..schema.master_schema import AgentModel, DatabaseModel
from ..config.config import GoogleClient, OpenAIClient

async def callModel(provider: int, agent: AgentModel):
    try:
        if provider == 0:
            agent_call = await asyncio.to_thread(GoogleClient().predict, agent=agent)
        else:
            agent_call = await asyncio.to_thread(OpenAIClient().predict, agent=agent)

        prepare_for_db = DatabaseModel(
            agent=agent.agent, content=agent_call, topic_id=agent.topic_id
        )
        await asyncio.to_thread(store_agent_response, prepare_for_db)
        return agent_call
    except Exception as e:
        logger.error(f"Error in callModel: {e}", exc_info=True)
        return {"error": str(e)}
