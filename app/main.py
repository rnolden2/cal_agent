"""
CAL - Collaborative AI Layer
"""

import asyncio
import os
import orjson
from agents import (
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
from agents.cal_master.cal_master_agent import MasterAgent
from schema.master_schema import AgentCallModel, AgentModel
from schema.master_schema import AgentTask
from llm.manager import callModel
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from typing import List

app = FastAPI()


@app.get("/")
def hello():
    return "hello"


@app.get("/ping")
def pingpong():
    return "pong"


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
