"""
CAL - Collaborative AI Layer
"""

import asyncio
import os
import orjson
import time
import uvicorn
from fastapi import FastAPI, logger
from pydantic import BaseModel, Field
from typing import Dict, Union, Any, Optional
from openai import OpenAI
import vertexai
from google.oauth2.service_account import Credentials
from vertexai.generative_models import GenerativeModel, GenerationConfig
from typing import List
from google.cloud import secretmanager
from google.cloud import firestore
from config.agent_list import AgentDescriptions, master_agent_description_prompt
from agents.cal_master.json_schema import json_schema as json_schema_master
from agents.customer_connect.json_schema import (
    json_schema as json_schema_customer_connect,
)
from agents.doc_master.json_schema import json_schema as json_schema_doc_master
from agents.editor.json_schema import json_schema as json_schema_editor
from agents.engineer.json_schema import json_schema as json_schema_engineer
from agents.pro_mentor.json_schema import json_schema as json_schema_pro_mentor
from agents.rival_watcher.json_schema import json_schema as json_schema_rival_watcher
from agents.sales_agent.json_schema import json_schema as json_schema_sales_agent
from agents.tech_wiz.json_schema import json_schema as json_schema_tech_wiz
from agents.trend_tracker.json_schema import json_schema as json_schema_trend_tracker


app = FastAPI()

credential_path = "app/config/api-project.json"
credentials = Credentials.from_service_account_file(credential_path)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credential_path
vertexai.init(
    project="api-project-371618", location="us-central1", credentials=credentials
)

# Initialize Firestore client
db = firestore.Client()


class AgentModel(BaseModel):
    agent: str
    role: str
    content: str
    agent_schema: Union[Dict, Any]
    additional_context: Optional[str] = None
    topic_id: Optional[str] = None


class AgentCallModel(BaseModel):
    provider: int
    response: str = Field(..., min_length=1)
    additional_context: Optional[str] = None
    topic_id: Optional[str] = None


class ProMentorAgentResponse(BaseModel):
    book_titles: str
    book_published_date: str


class DatabaseModel(BaseModel):
    agent: str
    content: Union[str, Dict]
    topic_id: Optional[str] = None


class AgentTask(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to handle the task.")
    prompt: str = Field(..., description="Task-specific prompt crafted for the agent.")
    additional_context: str = Field(
        "", description="Optional additional context for the task."
    )


class MasterAgentModel(BaseModel):
    content: str = Field(
        ..., description="The content or context provided by the user."
    )
    timestamp: int = Field(
        ..., description="The timestamp in milliseconds when the input was generated."
    )
    task_description: str = Field(
        ..., description="Summary of tasks derived from context."
    )
    agents_involved: List[str] = Field(
        ..., description="List of agent names involved in the task. Agents are"
    )
    tasks: List[AgentTask] = Field(
        ..., description="Tasks routed to individual agents."
    )


gpt_4o = "gpt-4o"
gpt_4o_mini = "gpt-4o-mini"
gemini_flash_002 = "gemini-1.5-flash-002"

openai_models = [gpt_4o, gpt_4o_mini]
google_models = [gemini_flash_002]


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


class OpenAIClient:
    def __init__(self):
        api_key = get_secret("openai_cal_key")
        self.client = OpenAI(api_key=api_key)

    def load_model(self, model_name: str | None):
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
        # if not message.parsed:
        #     raise ValueError(message.refusal)

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


def store_agent_response(response: DatabaseModel) -> str:
    """Store new response in Firestore database"""
    try:
        # Create a reference to the "test_task_events" collection
        collection_ref = db.collection("agent_responses")

        # Generate a custom document ID
        doc_ref = collection_ref.document()

        # Convert the TaskEvent object to a JSON string
        data = orjson.loads(response.content)

        # Include topic_id in the data
        if response.topic_id:
            data["topic_id"] = response.topic_id

        # Set data in the document
        doc_ref.set(data)

        doc_id = doc_ref.id

        # Update document with agent info, response_id and timestamp
        update_data = {
            "agent": response.agent,
            "response_id": doc_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
        }

        doc_ref.update(update_data)
        return doc_id
    # Handle any errors that occur during the Firestore operation
    except Exception as e:
        logger.error(f"Error writing to Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to write to database") from e


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


@app.get("/")
def hello():
    return "hello"


@app.get("/ping")
def pingpong():
    return "pong"


class MasterAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_master
        agent_model = AgentModel(
            role=master_agent_description_prompt,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.MASTER_AGENT.name,
        )
        return agent_model

    async def agent_queue(tasks: List[AgentTask], provider: str, topic_id: str = None):
        start = time.time()

        def process_task(task: AgentTask, topic_id: str = None):
            if task.agent_name == AgentDescriptions.CUSTOMER_CONNECT.name:
                response: AgentModel = CustomerConnect.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.DOC_MASTER.name:
                response = DocMaster.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.EDITOR_AGENT.name:
                response = EditorAgent.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.ENGINEER_AGENT.name:
                response = EngineerAgent.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.PRO_MENTOR.name:
                response = ProMentor.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.RIVAL_WATCHER.name:
                response = RivalWatcher.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.SALES_AGENT.name:
                response = SalesAgent.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.TECH_WIZ.name:
                response = TechWiz.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            elif task.agent_name == AgentDescriptions.TREND_TRACKER.name:
                response = TrendTracker.create_prompt(
                    task.prompt + " " + task.additional_context
                )
            else:
                response = None

            if response and topic_id:
                response.topic_id = topic_id
            return response  # Return the response

        responses = [process_task(task, topic_id=topic_id) for task in tasks]

        # Now gather the calls to callModel
        agent_responses = await asyncio.gather(
            *(
                callModel(agent=response, provider=provider)
                for response in responses
                if response
            )
        )

        # Use all agent responses to use when invoking the Professional Mentor Agent
        combined_response = "\n\n".join(agent_responses)
        # try:
        #     pro_mentor_prompt = ProMentor.create_prompt(combined_response)
        #     await callModel(agent=pro_mentor_prompt, provider=provider)
        # except Exception as e:
        #     print(f"Error calling ProMentor agent: {e}")

        end = time.time()
        time_length = end - start
        print(f"It took {time_length} seconds")
        return combined_response


@app.get("/master")
async def agentMaster(request: AgentCallModel):
    # Retrieve Master Agent
    agent_data: AgentModel = MasterAgent.create_prompt(request.response)
    agent_data.topic_id = request.topic_id
    master_agent_call = await callModel(agent=agent_data, provider=request.provider)
    response_dict = orjson.loads(master_agent_call)
    agent_data = response_dict["response"]["tasks"]
    tasks: List[AgentTask] = [AgentTask(**task) for task in agent_data]
    asyncio.create_task(
        MasterAgent.agent_queue(
            tasks=tasks, provider=request.provider, topic_id=request.topic_id
        )
    )
    return master_agent_call


class CustomerConnect:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_customer_connect
        agent_model = AgentModel(
            role=AgentDescriptions.CUSTOMER_CONNECT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.CUSTOMER_CONNECT.name,
        )
        return agent_model


@app.get("/customerconnect")
async def agentCustomerConnect(request: AgentCallModel):
    # Retrieve Customer Connect Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = CustomerConnect.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class DocMaster:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_doc_master
        agent_model = AgentModel(
            role=AgentDescriptions.DOC_MASTER.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.DOC_MASTER.name,
        )
        return agent_model


@app.get("/docmaster")
async def agentDocMaster(request: AgentCallModel):
    # Retrieve Trend Tracker Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = DocMaster.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class EditorAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_editor
        agent_model = AgentModel(
            role=AgentDescriptions.EDITOR_AGENT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.EDITOR_AGENT.name,
        )
        return agent_model


@app.get("/editor")
async def agentEditor(request: AgentCallModel):
    # Retrieve Editor Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = EditorAgent.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class EngineerAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_engineer
        agent_model = AgentModel(
            role=AgentDescriptions.ENGINEER_AGENT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.ENGINEER_AGENT.name,
        )
        return agent_model


@app.get("/engineer")
async def agentEngineer(request: AgentCallModel):
    # Retrieve Engineer Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = EngineerAgent.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class ProMentor:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_pro_mentor
        agent_model = AgentModel(
            role=AgentDescriptions.PRO_MENTOR.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.PRO_MENTOR.name,
        )
        return agent_model


@app.get("/promentor")
async def agentProMentor(request: AgentCallModel):
    # Retrieve Pro Mentor Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = ProMentor.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class RivalWatcher:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_rival_watcher
        agent_model = AgentModel(
            role=AgentDescriptions.RIVAL_WATCHER.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.RIVAL_WATCHER.name,
        )
        return agent_model


@app.get("/rivalwatcher")
async def agentRivalWatcher(request: AgentCallModel):
    # Retrieve Rival Watcher Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = RivalWatcher.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class SalesAgent:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_sales_agent
        agent_model = AgentModel(
            role=AgentDescriptions.SALES_AGENT.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.SALES_AGENT.name,
        )
        return agent_model


@app.get("/sales")
async def agentSales(request: AgentCallModel):
    # Retrieve Sales Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = SalesAgent.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class TechWiz:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_tech_wiz
        agent_model = AgentModel(
            role=AgentDescriptions.TECH_WIZ.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.TECH_WIZ.name,
        )
        return agent_model


@app.get("/techwiz")
async def agentTechWiz(request: AgentCallModel):
    # Retrieve Tech Wiz Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = TechWiz.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


class TrendTracker:
    def create_prompt(prompt: str) -> AgentModel:
        schema_to_use = json_schema_trend_tracker
        agent_model = AgentModel(
            role=AgentDescriptions.TREND_TRACKER.value,
            content=prompt,
            agent_schema=schema_to_use,
            agent=AgentDescriptions.TREND_TRACKER.name,
        )
        return agent_model


@app.get("/trendtracker")
async def agentTrendTracker(request: AgentCallModel):
    # Retrieve Trend Tracker Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = TrendTracker.create_prompt(prompt)
    agent_data.topic_id = request.topic_id
    agent_call = await callModel(agent=agent_data, provider=request.provider)
    return agent_call


if __name__ == "__main__":
    # Get the server port from the environment variable
    server_port = os.environ.get("PORT", "8080")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=int(server_port))
