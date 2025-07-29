"""
CAL - Collaborative AI Layer
"""

import orjson
import logging
import os
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Query, Request
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates

# from starlette.middleware.cors import CORSMiddleware

from .agent_schema.agent_master_schema import (
    AgentCallModel,
    AgentModel,
    DatabaseModel,
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
from .agents.reports.generator import generate_report_from_all_providers
from .storage.firestore_db import (
    get_agent_responses,
    set_topic_id,
    update_agent_document,
    store_agent_response,
)
from .utils.llm_counter import llm_call_counter, get_llm_call_counter


app = FastAPI()

logger = logging.getLogger(__name__)
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

# Load the market research template from file
try:
    template_path = os.path.join(
        os.path.dirname(__file__), "resources", "templates", "market_research.txt"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        MARKET_RESEARCH_TEMPLATE = f.read()
except FileNotFoundError:
    logger.error("Market research template file not found at %s", template_path)
    MARKET_RESEARCH_TEMPLATE = (
        "Market research template not found. Please check the file path."
    )


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/market-research")
async def market_research_page(request: Request):
    return templates.TemplateResponse(
        "market_research.html",
        {"request": request, "market_research_template": MARKET_RESEARCH_TEMPLATE},
    )


@app.get("/ping")
def pingpong():
    return "pong"


@app.post("/master")
async def agentMaster(request: AgentCallModel):
    try:
        llm_call_counter.set(0)
        # Retrieve Master Agent create tasks and have agents process them
        response = await MasterAgent.orchestrate_tasks(request)
        llm_calls = get_llm_call_counter()
        return {"response": response, "llm_calls": llm_calls}
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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
    return agent_call


@app.post("/engineer")
async def agentEngineer(request: AgentCallModel):
    # Retrieve Engineer Agent
    llm_call_counter.set(0)
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
    llm_calls = get_llm_call_counter()
    await MasterAgent.store_agent_response_in_db(
        agent_name=agent_data.agent,
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        response=agent_call,
    )
    return {"response": agent_call, "llm_calls": llm_calls}


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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
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
    MasterAgent.store_agent_response_in_db(
        topic_id=agent_data.topic_id,
        user_id=agent_data.user_id,
        agent_name=agent_data.agent,
        response=agent_call,
    )
    return agent_call


@app.post("/update-agent/{agent_id}")
async def update_agent(agent_id: str, update_data: UpdateAgentRequest):
    response = update_agent_document(agent_id, update_data)
    return response


@app.post("/generate-market-research")
async def generate_market_research(research_request: AgentCallModel):
    """
    Generates a market research report using the General agent from multiple providers,
    stores each report, and the final combined report.
    """
    llm_call_counter.set(0)
    # Generate the reports from all providers, which includes the combined report
    response = await generate_report_from_all_providers(
        research_request=research_request, template=MARKET_RESEARCH_TEMPLATE
    )

    # Generate a unique topic_id for this batch of reports
    topic_id = set_topic_id(None)
    user_id = "market-research-generator"

    # Store each individual report
    for report in response.get("reports", []):
        db_model = DatabaseModel(
            content=orjson.dumps(report).decode("utf-8"),
            topic_id=topic_id,
            user_id=user_id,
        )
        await store_agent_response(db_model)

    # Store the combined report
    if "combined_report" in response:
        combined_report_content = response["combined_report"]
        # Add a marker to identify this as the combined report in the DB
        if isinstance(combined_report_content, dict):
            combined_report_content["type"] = "combined_report"

        db_model_combined = DatabaseModel(
            content=orjson.dumps(combined_report_content).decode("utf-8"),
            topic_id=topic_id,
            user_id=user_id,
        )
        await store_agent_response(db_model_combined)

    llm_calls = get_llm_call_counter()
    response["llm_calls"] = llm_calls
    return response


@app.get(
    "/responses",
)
async def read_responses(
    topic_id: Optional[str] = Query(
        None, description="Only return responses for this topic_id"
    ),
    user_id: Optional[str] = Query(
        None, description="Only return responses for this user_id"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of responses to return (most recent first)",
    ),
) -> List[DatabaseModel]:
    """
    Fetch up to `limit` most-recent agent responses from Firestore,
    optionally filtered by topic_id and/or user_id.
    """
    return await get_agent_responses(topic_id=topic_id, user_id=user_id, limit=limit)


if __name__ == "__main__":
    # Get the server port from the environment variable
    server_port = os.environ.get("PORT", "8080")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=int(server_port))
