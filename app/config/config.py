import orjson
import os
from openai import OpenAI
from google import genai
from ..models.model_list import openai_models, google_models, perplexity_models
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
genai.Client(api_key=genai_api_key)


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
        self.client = None

    def load_model(self, model: int):
        """Loads the specified Gemini model."""
        try:
            if model:
                model_name = google_models[model]
                self.client = genai.GenerativeModel(model_name)  # Initialize the model
            else:
                model_name = google_models[0]
                self.client = genai.GenerativeModel(model_name)  # Initialize the model

        except IndexError:
            raise ValueError(
                f"Invalid model index: {model}. Must be within the range of available Google models."
            )
        except Exception as e:  # Catch other potential errors during model loading.
            raise RuntimeError(f"Failed to load Google model: {e}")

    def predict(self, agent: AgentModel):
        try:
            self.load_model(agent.model)
            completion = self.client.generate_content(
                agent.role + " : " + agent.content,
                generation_config=genai.GenerationConfig(
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

                # Create a new dictionary
                result = {
                    "context": agent.content,
                    "response": {
                        "content": response,
                        "citations": citations,
                        "provider": "perplexity",
                    },
                }
                return orjson.dumps(result)

        except httpx.HTTPError as e:
            raise RuntimeError(f"Perplexity API request failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Perplexity prediction failed: {e}") from e