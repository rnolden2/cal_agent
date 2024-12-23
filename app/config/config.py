import os
from typing import Union
from pydantic import BaseModel
from openai import OpenAI
import vertexai
from google.oauth2.service_account import Credentials
from vertexai.generative_models import GenerativeModel, GenerationConfig
from ..models.model_list import openai_models, google_models
from ..schema.master_schema import AgentModel
from google.cloud import secretmanager

# credential_path = "app/config/api-project.json"
# credentials = Credentials.from_service_account_file(credential_path)
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path

def get_secret(secret):
    client = secretmanager.SecretManagerServiceClient()
    project_id = "api-project-371618"
    secret_id = secret
    version_id = "latest"

    # Access the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})

    # Extract the secret value
    secret_value = response.payload.data.decode("UTF-8")

    # Use the secret value in your app
    # ...
    return secret_value

service_account = get_secret("cal-service-account")
vertexai.init(
    project="api-project-371618", location="us-central1", service_account=service_account
)

class OpenAIClient:
    def __init__(self):
        api_key = get_secret("openai_cal_key")
        self.client = OpenAI(api_key=api_key)

    def load_model(self, model_name: Union[str | None]):
        if model_name is None:
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
                    "name": "my_response",
                    "schema": agent.agent_schema,
                },
            },
        )
        message = completion.choices[0].message
        print(f"Response: {message.content}")
        return message.content

    def predict_pydantic_response(
        self, agent: AgentModel, response_format: BaseModel
    ) -> BaseModel:
        model = self.load_model(model_name=None)
        completion = self.client.beta.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": agent.role},
                {"role": "user", "content": agent.content},
            ],
            response_format=response_format,
        )
        message = completion.choices[0].message
        print(f"Response: {message.content}")
        if not message.parsed:
            raise ValueError(message.refusal)

        return message.parsed


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
        print(f"Response: {completion.text}")
        return completion.text
