"""
CAL - Collaborative AI Layer
"""
import os
import json
from agents import CustomerConnect, DocMaster, ProMentor, RivalWatcher, TechWiz, TrendTracker, MasterAgent
from schema.master_schema import AgentCallModel
from schema.cal_master_agent.pydantic_schema import AgentTask
from config.manager import callModel
from config.agent_list import AgentDescriptions
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from typing import List
app = FastAPI()


@app.get('/')
def hello():
    return "hello"


@app.get('/master')
def agentMaster(request:AgentCallModel):
    # Retrieve Customer Connect Agent
    agent_data = MasterAgent.create_prompt(request.response,request.provider)
    master_agent_call = callModel(agent=agent_data,provider=request.provider)
    response_dict = json.loads(master_agent_call)
    agent_data = response_dict["tasks"]
    tasks: List[AgentTask] = [AgentTask(**task) for task in agent_data]

    for task in tasks:
        if task.agent_name == AgentDescriptions.CUSTOMER_CONNECT.name:
            response = CustomerConnect.create_prompt(task.prompt + " " + task.additional_context, request.provider)
            agent_call = callModel(agent=response,provider=request.provider)
            print(agent_call)
        elif task.agent_name == AgentDescriptions.DOC_MASTER.name:
            response = DocMaster.create_prompt(task.prompt + " " + task.additional_context, request.provider)
            agent_call = callModel(agent=response,provider=request.provider)
            print(agent_call)
        elif task.agent_name == AgentDescriptions.PRO_MENTOR.name:
            response = ProMentor.create_prompt(task.prompt + " " + task.additional_context, request.provider)
            agent_call = callModel(agent=response,provider=request.provider)
            print(agent_call)
        elif task.agent_name == AgentDescriptions.RIVAL_WATCHER.name:
            response = RivalWatcher.create_prompt(task.prompt + " " + task.additional_context, request.provider)
            agent_call = callModel(agent=response,provider=request.provider)
            print(agent_call)
        elif task.agent_name == AgentDescriptions.TECH_WIZ.name:
            response = TechWiz.create_prompt(task.prompt + " " + task.additional_context, request.provider)
            agent_call = callModel(agent=response,provider=request.provider)
            print(agent_call)
        elif task.agent_name == AgentDescriptions.TREND_TRACKER.name:
            response = TrendTracker.create_prompt(task.prompt + " " + task.additional_context, request.provider)
            agent_call = callModel(agent=response,provider=request.provider)
            print(agent_call)
    return master_agent_call

@app.get('/customerconnect')
def agentCustomerConnect(request:AgentCallModel):
    # Retrieve Customer Connect Agent
    agent_data = CustomerConnect.create_prompt(request.response,request.provider)
    agent_call = callModel(agent=agent_data,provider=request.provider)
    return agent_call

@app.get('/docmaster')
def agentDocMaster(request:AgentCallModel):
    # Retrieve Trend Tracker Agent
    agent_data = DocMaster.create_prompt(request.response,request.provider)
    agent_call = callModel(agent=agent_data,provider=request.provider)
    return agent_call

@app.get('/promentor')
def agentProMentor(request:AgentCallModel):
    # Retrieve Pro Mentor Agent
    agent_data = ProMentor.create_prompt(request.response,request.provider)
    agent_call = callModel(agent=agent_data,provider=request.provider)
    return agent_call

@app.get('/rivalwatcher')
def agentRivalWatcher(request:AgentCallModel):
    # Retrieve Rival Watcher Agent
    agent_data = RivalWatcher.create_prompt(request.response,request.provider)
    agent_call = callModel(agent=agent_data,provider=request.provider)
    return agent_call
    
@app.get('/techwiz')
def agentTechWiz(request:AgentCallModel):
    # Retrieve Tech Wiz Agent
    agent_data = TechWiz.create_prompt(request.response,request.provider)
    agent_call = callModel(agent=agent_data,provider=request.provider)
    return agent_call
    
@app.get('/trendtracker')
def agentTrendTracker(request:AgentCallModel):
    # Retrieve Trend Tracker Agent
    agent_data = TrendTracker.create_prompt(request.response,request.provider)
    agent_call = callModel(agent=agent_data,provider=request.provider)
    return agent_call
    
if __name__ == "__main__":
    # Get the server port from the environment variable
    server_port = os.environ.get("PORT", "8080")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=int(server_port))
