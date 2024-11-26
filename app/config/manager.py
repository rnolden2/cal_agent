from schema.master_schema import AgentModel
from config.config import GoogleClient, OpenAIClient

def callModel(provider:int, agent:AgentModel):
    if provider == 0:
        return GoogleClient().predict(agent=agent)
    else:
        return OpenAIClient().predict(agent=agent)
