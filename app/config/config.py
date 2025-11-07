import asyncio
import orjson
import os
from openai import OpenAI
from google import genai
from xai_sdk import Client
from xai_sdk.chat import user, system
from ..models.model_list import openai_models, google_models, perplexity_models, xai_models
from ..agent_schema.agent_master_schema import AgentModel
from google.cloud import secretmanager
import httpx


def get_secret(secret):
    # credential_path = "app/config/api-project.json"
    # Set the environment variable for authentication
    
    client = secretmanager.SecretManagerServiceClient()
    project_id = "api-project-371618"
    secret_id = secret
    version_id = "latest"

    # Access the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})

    # Extract the secret value
    secret_value = response.payload.data.decode("UTF-8")
    return secret_value


genai_api_key = get_secret("gemini_api")
google_client = genai.Client(api_key=genai_api_key)


class OpenAIClient:
    def __init__(self):
        api_key = get_secret("openai_cal_key")
        self.client = OpenAI(api_key=api_key)
        self.model = None  # Initialize model to None

    def load_model(self, model: int):
        """Loads the specified OpenAI model."""
        try:
            if model:
                self.model = openai_models[model]  # Set the model attribute
            else:
                self.model = openai_models[0]  # Set the model to default

        except IndexError:
            raise ValueError(
                f"Invalid model index: {model}. Must be within the range of available OpenAI models."
            )
        except Exception as e:  # Handle other potential errors
            raise RuntimeError(f"Failed to load OpenAI model: {e}")

    def predict(self, agent: AgentModel):
        try:
            self.load_model(agent.model)
            completion = self.client.beta.chat.completions.parse(
                model=self.model,  # Use the loaded model
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
        except Exception as e:
            raise RuntimeError(f"OpenAI prediction failed: {e}")


class GoogleClient:
    def __init__(self):
        # Initialize
        self.model_name = None

    def load_model(self, model: int):
        """Loads the specified Gemini model name."""
        try:
            if model:
                self.model_name = google_models[model]
            else:
                self.model_name = google_models[0]

        except IndexError:
            raise ValueError(
                f"Invalid model index: {model}. Must be within the range of available Google models."
            )
        except Exception as e:  # Catch other potential errors during model loading.
            raise RuntimeError(f"Failed to load Google model: {e}")

    def predict(self, agent: AgentModel):
        try:
            self.load_model(agent.model)
            completion = google_client.models.generate_content(
                model=self.model_name,
                contents=agent.role + " : " + agent.content,
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=agent.agent_schema,
                ),
            )
            # print(f"Response: {completion.text}")
            return completion.text
        except Exception as e:
            raise RuntimeError(f"Google prediction failed: {e}")


class PerplexityClient:
    url = "https://api.perplexity.ai/chat/completions"

    def __init__(self):
        self.pplx_api_key = get_secret("pplx-api-key")

    def load_model(self, model: int):
        """Loads the specified Perplexity model."""
        try:
            model_name = perplexity_models[model]
            return model_name
        except IndexError:
            raise ValueError(
                f"Invalid model index: {model}. Must be within the range of available Perplexity models."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load Perplexity model: {e}")

    async def predict(self, agent: AgentModel):  # Make predict async
        try:
            model = self.load_model(agent.model)
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": agent.role},
                    {"role": "user", "content": agent.content},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "my_response",
                        "schema": agent.agent_schema,
                    },
                },
                "search_domain_filter": ["perplexity.ai"],
                "return_images": False,
                "return_related_questions": False,
            }
            headers = {
                "Authorization": "Bearer " + self.pplx_api_key,
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.url, headers=headers, json=payload, timeout=600.0
                )
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                data = response.json()
                response = data["choices"][0]["message"]["content"]
                citations = data["citations"]
                search_results = data["search_results"]

                # Create a new dictionary
                result = {
                    "context": agent.content,
                    "response": {
                        "content": response,
                        "citations": citations,
                        "search_results": search_results,
                        "provider": "perplexity",
                    },
                }
                return orjson.dumps(result)

        except httpx.HTTPError as e:
            raise RuntimeError(f"Perplexity API request failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Perplexity prediction failed: {e}") from e

class XAIClient:
    def __init__(self):
        self.api_key = get_secret("XAI_API_KEY")  # Assuming get_secret is available
        self.client = Client(api_key=self.api_key, timeout=3600)
        self.model = None

    def load_model(self, model: int):
        try:
            if model:
                self.model = xai_models[model]
            else:
                self.model = xai_models[0]
        except IndexError:
            raise ValueError(
                f"Invalid model index: {model}. Must be within the range of available XAI models."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load XAI model: {e}")

    async def predict(self, agent: AgentModel):
        try:
            self.load_model(agent.model)
            chat = self.client.chat.create(model=self.model)
            chat.append(system(agent.role))
            chat.append(user(agent.content))
            response = await asyncio.to_thread(chat.sample)
            return response.content
        except Exception as e:
            raise RuntimeError(f"XAI prediction failed: {e}")