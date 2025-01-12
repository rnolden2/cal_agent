import os
import orjson
from typing import Union
from pydantic import BaseModel
from openai import OpenAI
import google.generativeai as genai
from ..models.model_list import openai_models, google_models, perplexity_models
from ..agent_schema.agent_master_schema import AgentModel
from google.cloud import secretmanager
import httpx


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


genai_api_key = get_secret("gemini_api")
genai.configure(api_key=genai_api_key)


class OpenAIClient:
    def __init__(self):
        api_key = get_secret("openai_cal_key")
        self.client = OpenAI(api_key=api_key)
        self.model = None  # Initialize model to None

    def load_model(self, model: int):
        """Loads the specified OpenAI model."""
        try:
            self.model = openai_models[model]  # Set the model attribute
            return self.model  # Return the loaded model name for informational purposes

        except IndexError:
            raise ValueError(
                f"Invalid model index: {model}. Must be within the range of available OpenAI models."
            )
        except Exception as e:  # Handle other potential errors
            raise RuntimeError(f"Failed to load OpenAI model: {e}")

    def predict(self, agent: AgentModel, model: int):
        try:
            self.load_model(model)
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
        # Initialize
        self.client = None

    def load_model(self, model: int):
        """Loads the specified Gemini model."""
        try:
            model_name = google_models[model]
            self.client = genai.GenerativeModel(model_name)  # Initialize the model
            return model_name

        except IndexError:
            raise ValueError(
                f"Invalid model index: {model}. Must be within the range of available Google models."
            )
        except Exception as e:  # Catch other potential errors during model loading.
            raise RuntimeError(f"Failed to load Google model: {e}")

    def predict(self, agent: AgentModel, model: int):
        try:
            self.load_model(model)
            completion = self.client.generate_content(
                agent.role + " : " + agent.content,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=agent.agent_schema,
                ),
            )
            print(f"Response: {completion.text}")
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

    async def predict(self, agent: AgentModel, model: int):  # Make predict async
        try:
            model = self.load_model(model)
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
                content = data["choices"][0]["message"]["content"]
                citations = data["citations"]

                # Create a new dictionary
                result = {
                    "content": content,
                    "citations": citations,
                    "provider": "perplexity",
                }
                return orjson.dumps(result)

        except httpx.HTTPError as e:
            raise RuntimeError(f"Perplexity API request failed: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Perplexity prediction failed: {e}") from e


Response = {
    "context": "Customer requested a ROM for an existing blower, comparing to NASA contract and avoiding NRE costs.",
    "timestamp": 1701234567890,
    "response_id": "response-1701234567890",
    "response": {
        "email": "Subject: Update on Customer's Request for ROM on Blower\n\nDear Team,\n\nI hope this message finds you well. I am writing to provide you with an update on the recent customer inquiry regarding a Rough Order of Magnitude (ROM) for one of our existing blower units.\n\nThe customer has specifically requested a ROM estimate and expressed interest in aligning the terms with our previous contract conditions established during the collaboration with NASA. Notably, they are keen on exploring solutions that avoid Non-Recurring Engineering (NRE) costs, aligning with their current budgeting constraints.\n\nOur customer is actively strategizing their budget allocations and has emphasized their preference to forego any additional NRE expenses associated with this request. Please take this into consideration as we proceed with preparing their estimate.\n\nI am keen to discuss further steps and would appreciate any insights or considerations you might have.\n\nThank you for your attention to this request.\n\nBest regards,\n\n[Your Name]\n[Your Position]\n[Your Contact Information]",
        "follow_up": {
            "days_to_wait": 5,
            "suggestions": "Consider reaching out to the customer to discuss any specific details they might want to prioritize in the ROM. After providing the ROM, follow up to offer any assistance needed in understanding the cost breakdown, especially concerning NRE avoidance.",
        },
    },
}
Response = {
    "context": "Retrieve and verify the details of the Calnetix contract with NASA for the CO2 scrubber blower on the ISS, particularly focusing on the price mentioned as 361. Check the website USAspending.gov to confirm the contract details.",
    "timestamp": 1700746314455,
    "response_id": "response-1700746314455",
    "response": {
        "improvement": {
            "personally": {
                "description": "Suggestions for personal improvement.",
                "explanation": "Enhancing efficiency in retrieving and verifying information requires developing certain personal skills.",
                "actions": [
                    "Improve time management skills to handle requests more efficiently.",
                    "Develop attention to detail to minimize errors in data verification.",
                    "Enhance problem-solving skills to find solutions when information is not readily available.",
                    "Cultivate patience and persistence when conducting thorough research.",
                    "Set up a quiet workspace to improve concentration and accuracy.",
                    "Practice mindfulness or meditation to improve focus and reduce stress.",
                    "Create a checklist to ensure all steps in the retrieval process are followed.",
                    "Keep track of performance over time to identify areas that need improvement.",
                    "Regularly review and update personal knowledge regarding databases and retrieval methods.",
                    "Engage in leisure reading to enhance comprehension skills and processing speed.",
                ],
            },
            "professionally": {
                "description": "Suggestions for professional improvement.",
                "explanation": "Improving the ability to manage a document retrieval service involves acquiring new skills and tools that increase efficiency and accuracy.",
                "actions": [
                    "Attend a workshop on effective research and information retrieval techniques.",
                    "Learn advanced search functionalities on platforms like USAspending.gov.",
                    "Take a course in data analytics to better interpret contracts and financial information.",
                    "Develop a systematic filing system for organizing contracts and related documents.",
                    "Implement quality control procedures to ensure accuracy of information retrieved.",
                    "Network with professionals in the field to exchange tips and insights.",
                    "Stay updated on changes in government and military contracting processes.",
                    "Invest in software tools that enhance document management capabilities.",
                    "Regularly review and adjust operational procedures to align with best practices.",
                    "Participate in continuing education opportunities related to document management and retrieval.",
                ],
            },
        },
        "past_feedback": "This task involves verifying contract information from a specific government website, which is similar to previous requests involving the retrieval of contract details or verification of financial information from trusted databases.",
    },
}
Response = {
    "context": "the user needs to prioritize a task involving communicating and managing customer expectations about budgeting and NRE (Non-Recurring Engineering) costs, while also maintaining trust by being transparent about contract discrepancies.",
    "timestamp": 1701200000000,
    "response_id": "1701200000000_abc123",
    "response": {
        "improvement": {
            "personally": {
                "explanation": "Improving personally in managing stressful interactions with customers about sensitive topics like budgeting and NRE costs can help maintain calmness and clarity in communication.",
                "actions": [
                    "Practice active listening to fully understand the customer's concerns and questions.",
                    "Prepare emotionally for these discussions by recognizing stress triggers and managing them.",
                    "Rehearse potential conversations to build confidence in your communication skills.",
                    "Seek feedback from colleagues on your communication effectiveness to identify areas for improvement.",
                    "Keep a journal to reflect on these interactions and track your personal growth.",
                    "Enhance your negotiation skills through workshops or online courses.",
                    "Stay informed about industry standards on budgeting and NRE costs to communicate more effectively.",
                    "Develop empathy by considering the customer's perspective during these interactions.",
                    "Learn stress management techniques such as deep breathing or mindfulness to stay calm under pressure.",
                    "Engage in regular self-care activities to maintain overall well-being.",
                ],
            },
            "professionally": {
                "explanation": "Professionally, improving by setting clear priorities and managing tasks efficiently will help keep on top of workload while effectively communicating with customers about budgeting and NRE costs.",
                "actions": [
                    "Use a task management tool to list and prioritize all current tasks, marking this task as high priority.",
                    "Allocate specific blocks of time in your schedule dedicated to this task to ensure focused attention.",
                    "Break down the task into smaller, manageable activities with clear deadlines.",
                    "Gather all necessary contract documentation and notes ahead to avoid last-minute scrambling.",
                    "Prepare a transparent communication outline that clearly explains the discrepancies and proposed solutions.",
                    "Set up a meeting with the customer to discuss findings in an organized manner.",
                    "Prepare FAQ sheets on NRE costs and budgeting to quickly address common queries from customers.",
                    "Keep documentation organized and accessible to support transparency and trust.",
                    "Regularly update your progress on the task and share it with stakeholders to keep them informed.",
                    "Seek advice or mentorship from a more experienced colleague if needed on handling complex customer interactions.",
                ],
            },
        },
        "past_feedback": "Previously, I advised focusing on building strong communication skills and prioritizing tasks strategically. In this situation, this advice remains relevant as you need to prioritize this customer-related task and effectively communicate sensitive financial details.",
    },
}
