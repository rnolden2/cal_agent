from openai import OpenAI
import vertexai
from google.oauth2.service_account import Credentials
from vertexai.generative_models import GenerativeModel, GenerationConfig
from models.model_list import openai_models, google_models
from schema.openai_schema import ChatCompletion, Message
from schema.master_schema import AgentModel


credentials = Credentials.from_service_account_file(
    "app/config/api-project.json"
)
vertexai.init(
    project="", location="us-central1", credentials=credentials
)


class OpenAIClient:
    def __init__(self):
        api_key = ""
        self.client = OpenAI(api_key=api_key)

    def load_model(self, model_name: str | None):
        if model_name == None:
            return openai_models[1]
        else:
            return openai_models[0]

    def predict(self, agent: AgentModel):
        model = self.load_model(model_name=None)
        completion = self.client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": agent.role},
                {"role": "user", "content": agent.content},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "math_response",
                    "schema": agent.agent_schema,
                },
            },
        )
        chat_completion = completion.choices[0].message.content
        print(f"Response: {chat_completion}")
        return chat_completion


class GoogleClient:
    def __init__(self):
        self.client = GenerativeModel(google_models[0])

    def predict(self, agent: AgentModel):
        completion = self.client.generate_content(
            agent.role + " : " + agent.content,
            generation_config=GenerationConfig(
                response_mime_type="application/json",
                response_schema=agent.agent_schema,
            ),
        )
        return completion.text
