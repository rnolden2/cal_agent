"""
CAL - Collaborative AI Layer
"""

import logging
import os

import uvicorn
from fastapi import FastAPI
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from starlette.middleware.cors import CORSMiddleware

from .agent_schema.agent_master_schema import (
    AgentCallModel,
    AgentModel,
    UpdateAgentRequest,
)
from .agents import (
    CustomerConnect,
    DocMaster,
    EditorAgent,
    EngineerAgent,
    ProMentor,
    RivalWatcher,
    SalesAgent,
    TechWiz,
    TrendTracker,
)
from .agents.cal_master.master import MasterAgent
from .llm.manager import callModel
from .storage.firestore_db import set_topic_id, update_agent_document

app = FastAPI()

logger = logging.getLogger(__name__)


@app.get("/")
def hello():
    return "hello"


@app.get("/ping")
def pingpong():
    return "pong"


@app.post("/master")
async def agentMaster(request: AgentCallModel):
    try:
        # Retrieve Master Agent create tasks and have agents process them
        response = await MasterAgent.orchestrate_tasks(request)
        return response
    except Exception as e:
        logger.error(f"Error in agentMaster endpoint: {e}", exc_info=True)
        return {"error": str(e)}


@app.post("/customerconnect")
async def agentCustomerConnect(request: AgentCallModel):
    # Retrieve Customer Connect Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = CustomerConnect.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/docmaster")
async def agentDocMaster(request: AgentCallModel):
    # Retrieve Trend Tracker Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = DocMaster.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/editor")
async def agentEditor(request: AgentCallModel):
    # Retrieve Editor Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = EditorAgent.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/engineer")
async def agentEngineer(request: AgentCallModel):
    # Retrieve Engineer Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = EngineerAgent.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/promentor")
async def agentProMentor(request: AgentCallModel):
    # Retrieve Pro Mentor Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = ProMentor.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/rivalwatcher")
async def agentRivalWatcher(request: AgentCallModel):
    # Retrieve Rival Watcher Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = RivalWatcher.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/sales")
async def agentSales(request: AgentCallModel):
    # Retrieve Sales Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = SalesAgent.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/techwiz")
async def agentTechWiz(request: AgentCallModel):
    # Retrieve Tech Wiz Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = TechWiz.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/trendtracker")
async def agentTrendTracker(request: AgentCallModel):
    # Retrieve Trend Tracker Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = TrendTracker.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id, agent_data.provider, agent_data.model = (
        set_topic_id(request.topic_id),
        request.user_id,
        request.provider,
        request.model,
    )
    agent_call = await callModel(agent=agent_data)
    return agent_call


@app.post("/update-agent/{agent_id}")
async def update_agent(agent_id: str, update_data: UpdateAgentRequest):
    response = update_agent_document(agent_id, update_data)
    return response


if __name__ == "__main__":
    # Get the server port from the environment variable
    server_port = os.environ.get("PORT", "8080")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=int(server_port))
