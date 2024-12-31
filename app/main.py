"""
CAL - Collaborative AI Layer
"""

import asyncio
import os
import orjson
import logging

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
from .agents.cal_master.cal_master_agent import MasterAgent
from .agent_schema.agent_master_schema import AgentCallModel, AgentModel
from .agent_schema.agent_master_schema import AgentTask
from .storage.firestore_db import set_topic_id
from .llm.manager import callModel
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from typing import List

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
        # Retrieve Master Agent
        agent_data: AgentModel = MasterAgent.create_prompt(request.response)
        agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
        master_agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
        response_dict = orjson.loads(master_agent_call)
        agent_data = response_dict["response"]["tasks"]
        tasks: List[AgentTask] = [AgentTask(**task) for task in agent_data]
        asyncio.create_task(
            MasterAgent.agent_queue(
                tasks=tasks, provider=request.provider, topic_id=request.topic_id, model=request.model, user_id=request.user_id
            )
        )
        return master_agent_call
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
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/docmaster")
async def agentDocMaster(request: AgentCallModel):
    # Retrieve Trend Tracker Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = DocMaster.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/editor")
async def agentEditor(request: AgentCallModel):
    # Retrieve Editor Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = EditorAgent.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/engineer")
async def agentEngineer(request: AgentCallModel):
    # Retrieve Engineer Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = EngineerAgent.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/promentor")
async def agentProMentor(request: AgentCallModel):
    # Retrieve Pro Mentor Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = ProMentor.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/rivalwatcher")
async def agentRivalWatcher(request: AgentCallModel):
    # Retrieve Rival Watcher Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = RivalWatcher.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/sales")
async def agentSales(request: AgentCallModel):
    # Retrieve Sales Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = SalesAgent.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/techwiz")
async def agentTechWiz(request: AgentCallModel):
    # Retrieve Tech Wiz Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = TechWiz.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


@app.post("/trendtracker")
async def agentTrendTracker(request: AgentCallModel):
    # Retrieve Trend Tracker Agent
    prompt = request.response
    if request.additional_context:
        prompt += " " + request.additional_context

    agent_data: AgentModel = TrendTracker.create_prompt(prompt)
    agent_data.topic_id, agent_data.user_id = set_topic_id(request.topic_id), request.user_id
    agent_call = await callModel(agent=agent_data, provider=request.provider, model=request.model)
    return agent_call


if __name__ == "__main__":
    # Get the server port from the environment variable
    server_port = os.environ.get("PORT", "8080")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=int(server_port))
