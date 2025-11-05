import asyncio
from ..llm.manager import callModel
from ..agent_schema.agent_master_schema import AgentModel, Provider

async def test_grok():
    agent = AgentModel(
        agent="test",
        role="You are a helpful assistant.",
        content="What is 2 + 2?",
        agent_schema={},
        model=0,  
        provider=Provider.XAI
    )
    response = await callModel(agent)
    print("Grok response:", response)

if __name__ == "__main__":
    asyncio.run(test_grok())
