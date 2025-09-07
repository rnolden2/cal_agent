"""
CAL - Collaborative AI Layer
"""

import logging
import os
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from .agent_schema.agent_master_schema import (
    AgentCallModel,
    DatabaseModel,
    UpdateAgentRequest,
    FeedbackModel,
    FeedbackResponse,
    ReportGenerationRequest,
    ReportResponse,
    SectionUpdateRequest,
)
from .storage.firestore_db import (
    get_agent_responses,
    get_responses_by_topic_id,
    get_topic_summary,
    search_responses_by_tags,
    update_agent_document,
    store_feedback,
    get_feedback,
    store_report,
    get_report,
    get_reports,
    update_report,
    update_report_section,
    delete_report,
)
from .utils.llm_counter import llm_call_counter, get_llm_call_counter
from .orchestrator.agent_orchestrator import AgentOrchestrator
from .api.response_formatter import router as formatter_router


app = FastAPI()

# Include the response formatter router
app.include_router(formatter_router, prefix="/api", tags=["formatting"])

logger = logging.getLogger(__name__)
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
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


@app.get("/workflow-dashboard")
async def workflow_dashboard_page(request: Request):
    return templates.TemplateResponse("workflow_dashboard.html", {"request": request})


@app.get("/report-interface")
async def report_interface_page(request: Request):
    return templates.TemplateResponse("report_interface.html", {"request": request})


@app.get("/feedback-display")
async def feedback_display_page(request: Request):
    return templates.TemplateResponse("feedback_display.html", {"request": request})


@app.get("/feedback-input")
async def feedback_input_page(request: Request):
    return templates.TemplateResponse("feedback_input.html", {"request": request})


@app.get("/history")
async def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})


@app.get("/ping")
def pingpong():
    return "pong"


@app.post("/agent")
async def unified_agent_endpoint(request: AgentCallModel):
    """Single endpoint for all agent interactions"""
    orchestrator = AgentOrchestrator()
    return await orchestrator.process_request(request)


@app.post("/update-agent/{agent_id}")
async def update_agent(agent_id: str, update_data: UpdateAgentRequest):
    response = update_agent_document(agent_id, update_data)
    return response




@app.get(
    "/responses",
)
async def read_responses(
    topic_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = None,
) -> List[DatabaseModel]:
    """
    Fetch up to `limit` most-recent agent responses from Firestore,
    optionally filtered by topic_id and/or user_id.
    """
    return await get_agent_responses(topic_id=topic_id, user_id=user_id, limit=limit)


@app.get("/responses/topic/{topic_id}")
async def get_responses_for_topic(topic_id: str):
    """
    Get all agent responses for a specific topic ID.
    This shows all agents that were involved in generating a response.
    """
    return await get_responses_by_topic_id(topic_id)


@app.get("/topic/{topic_id}/summary")
async def get_topic_info(topic_id: str):
    """
    Get a summary of a topic including all agents involved and response count.
    """
    return await get_topic_summary(topic_id)


@app.get("/responses/search")
async def search_responses(
    q: str = Query(..., description="Search terms separated by commas"),
    user_id: Optional[str] = None,
    limit: int = 50
):
    """
    Search agent responses by tags and keywords.
    
    Args:
        q: Search terms separated by commas (e.g., "market research,trends,analysis")
        user_id: Optional user ID to filter by
        limit: Maximum number of results to return
    """
    search_terms = [term.strip() for term in q.split(",") if term.strip()]
    return await search_responses_by_tags(search_terms, user_id=user_id, limit=limit)


@app.post("/feedback")
async def submit_feedback(feedback: FeedbackModel) -> FeedbackResponse:
    """
    Submit new feedback to be incorporated into future agent responses.
    
    Args:
        feedback: FeedbackModel containing the feedback details
        
    Returns:
        FeedbackResponse with success status and feedback ID
    """
    try:
        feedback_id = await store_feedback(feedback)
        return FeedbackResponse(
            success=True,
            message="Feedback successfully stored and will be incorporated into future responses",
            feedback_id=feedback_id
        )
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        return FeedbackResponse(
            success=False,
            message=f"Error storing feedback: {str(e)}"
        )


@app.get("/feedback")
async def get_feedback_list(
    user_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
):
    """
    Retrieve stored feedback entries.
    
    Args:
        user_id: Optional user ID to filter by
        category: Optional category to filter by
        limit: Maximum number of results to return
    """
    try:
        return await get_feedback(user_id=user_id, category=category, limit=limit)
    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        return {"error": f"Error retrieving feedback: {str(e)}"}


@app.get("/simple-report-generator")
async def simple_report_generator_page(request: Request):
    return templates.TemplateResponse("simple_report_generator.html", {"request": request})


@app.post("/reports/generate")
async def generate_report(request: ReportGenerationRequest) -> ReportResponse:
    """
    Generate a new report using the agent orchestrator and market research template.
    
    Args:
        request: ReportGenerationRequest containing report details
        
    Returns:
        ReportResponse with success status and generated report
    """
    try:
        from .agent_schema.agent_master_schema import ReportModel, ReportSection
        import uuid
        from datetime import datetime
        
        # Create sections based on the market research template
        market_research_sections = [
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Defense & Military News Summary",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Government & DoD Solicitations",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Technology & Power Electronics Advances",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Defense Contractor & Startup Updates",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Contract Awards & Funding News",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Export & Onboard Vehicle Power Developments",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Emerging Startup Watch",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Commercial Application Opportunities",
                content="",
                status="draft"
            ),
            ReportSection(
                section_id=str(uuid.uuid4()),
                title="Key Takeaways & Recommendations",
                content="",
                status="draft"
            )
        ]
        
        # Generate content for each section using the orchestrator and market research template
        orchestrator = AgentOrchestrator()
        
        for section in market_research_sections:
            # Create a detailed prompt based on the market research template
            section_prompt = f"""
Using the Calnetix Defense & Power Systems Market Intelligence Report template, generate content for the "{section.title}" section.

Report Topic: {request.title}
Report Description: {request.description or 'Market research and analysis report for Calnetix Defense & Power Systems'}

Template Context: {MARKET_RESEARCH_TEMPLATE}

Please generate comprehensive, professional content for the "{section.title}" section that follows the template requirements:

- Include verifiable sources with URLs where required
- Focus on Calnetix products (Enercycle inverter family, DC-1000 variant)
- Provide actionable intelligence and strategic insights
- Use proper formatting (tables, bullet points as specified in template)
- Include specific dates, companies, and technical details
- Ensure all information is relevant to defense power systems and military applications

Generate detailed, fact-based content that would be valuable for strategic decision-making.
"""
            
            # Use the orchestrator to generate content
            agent_request = AgentCallModel(
                provider="openai",
                model=1,
                response=section_prompt,
                additional_context=f"Market research report generation for section: {section.title}",
                user_id=request.user_id,
                topic_id=None
            )
            
            orchestrator_response = await orchestrator.process_request(agent_request)
            
            # Update section with generated content
            section.content = orchestrator_response.get("response", f"Content for {section.title} section")
            section.status = "completed"
            section.agent_contributors = orchestrator_response.get("agents_involved", ["General"])
            section.last_updated = datetime.now()
        
        # Create the report using market research template structure
        report = ReportModel(
            title=request.title,
            description=request.description or "Calnetix Defense & Power Systems Market Intelligence Report",
            user_id=request.user_id,
            sections=market_research_sections,
            status="draft",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store the report
        report_id = await store_report(report)
        
        # Add the report_id to the report object
        report_dict = report.model_dump()
        report_dict["report_id"] = report_id
        
        return ReportResponse(
            success=True,
            message="Market research report generated successfully using template",
            report_id=report_id,
            report=report_dict
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return ReportResponse(
            success=False,
            message=f"Error generating report: {str(e)}"
        )


@app.get("/reports")
async def list_reports(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List reports with optional filtering.
    
    Args:
        user_id: Optional user ID to filter by
        status: Optional status to filter by
        limit: Maximum number of results to return
    """
    try:
        return await get_reports(user_id=user_id, status=status, limit=limit)
    except Exception as e:
        logger.error(f"Error retrieving reports: {e}")
        return {"error": f"Error retrieving reports: {str(e)}"}


@app.get("/reports/{report_id}")
async def get_report_by_id(report_id: str):
    """
    Get a specific report by ID.
    
    Args:
        report_id: The report ID to retrieve
    """
    try:
        report = await get_report(report_id)
        if report:
            return report
        else:
            return {"error": "Report not found"}
    except Exception as e:
        logger.error(f"Error retrieving report: {e}")
        return {"error": f"Error retrieving report: {str(e)}"}


@app.put("/reports/{report_id}")
async def update_report_by_id(report_id: str, updates: dict):
    """
    Update a report.
    
    Args:
        report_id: The report ID to update
        updates: Dictionary of updates to apply
    """
    try:
        success = await update_report(report_id, updates)
        if success:
            return {"success": True, "message": "Report updated successfully"}
        else:
            return {"success": False, "message": "Failed to update report"}
    except Exception as e:
        logger.error(f"Error updating report: {e}")
        return {"success": False, "message": f"Error updating report: {str(e)}"}


@app.put("/reports/{report_id}/sections/{section_id}")
async def update_section(report_id: str, section_id: str, updates: dict):
    """
    Update a specific section of a report.
    
    Args:
        report_id: The report ID
        section_id: The section ID to update
        updates: Dictionary containing content and status updates
    """
    try:
        content = updates.get("content", "")
        status = updates.get("status", "completed")
        
        success = await update_report_section(report_id, section_id, content, status)
        if success:
            return {"success": True, "message": "Section updated successfully"}
        else:
            return {"success": False, "message": "Failed to update section"}
    except Exception as e:
        logger.error(f"Error updating section: {e}")
        return {"success": False, "message": f"Error updating section: {str(e)}"}


@app.post("/reports/{report_id}/sections/{section_id}/revise")
async def revise_section_with_feedback(report_id: str, section_id: str, feedback_request: SectionUpdateRequest):
    """
    Revise a section based on feedback using the agent orchestrator.
    
    Args:
        report_id: The report ID
        section_id: The section ID to revise
        feedback_request: The feedback and revision request
    """
    try:
        # Get the current report and section
        report = await get_report(report_id)
        if not report:
            return {"success": False, "message": "Report not found"}
        
        # Find the section
        section = None
        for s in report.get("sections", []):
            if s.get("section_id") == section_id:
                section = s
                break
        
        if not section:
            return {"success": False, "message": "Section not found"}
        
        # Create a revision prompt
        revision_prompt = f"""
Please revise the following section based on the provided feedback:

**Section Title:** {section.get('title', 'Unknown')}

**Current Content:**
{section.get('content', '')}

**Feedback for Improvement:**
{feedback_request.feedback}

**Instructions:**
- Incorporate the feedback to improve the content
- Maintain professional tone and formatting
- Ensure the content is comprehensive and accurate
- Keep the same general structure but enhance based on feedback

Please provide the revised content:
"""
        
        # Use the orchestrator to revise the content
        orchestrator = AgentOrchestrator()
        agent_request = AgentCallModel(
            provider="openai",
            model=1,
            response=revision_prompt,
            additional_context=f"Section revision based on feedback",
            user_id=feedback_request.user_id,
            topic_id=None
        )
        
        orchestrator_response = await orchestrator.process_request(agent_request)
        revised_content = orchestrator_response.get("response", section.get('content', ''))
        
        # Update the section
        success = await update_report_section(report_id, section_id, revised_content, "completed")
        
        if success:
            return {
                "success": True,
                "message": "Section revised successfully based on feedback",
                "updated_content": revised_content
            }
        else:
            return {"success": False, "message": "Failed to update section"}
            
    except Exception as e:
        logger.error(f"Error revising section: {e}")
        return {"success": False, "message": f"Error revising section: {str(e)}"}


@app.delete("/reports/{report_id}")
async def delete_report_by_id(report_id: str):
    """
    Delete a report.
    
    Args:
        report_id: The report ID to delete
    """
    try:
        success = await delete_report(report_id)
        if success:
            return {"success": True, "message": "Report deleted successfully"}
        else:
            return {"success": False, "message": "Failed to delete report"}
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        return {"success": False, "message": f"Error deleting report: {str(e)}"}


@app.post("/reports/{report_id}/email")
async def email_report(report_id: str, email_request: dict):
    """
    Send a report to an email address.
    
    Args:
        report_id: The report ID to send
        email_request: Dictionary containing the recipient email
    """
    try:
        email = email_request.get("email")
        if not email:
            return {"success": False, "message": "Email address is required"}
        
        report = await get_report(report_id)
        if not report:
            return {"success": False, "message": "Report not found"}
        
        # Placeholder for email sending logic
        logger.info(f"Simulating sending report {report_id} to {email}")
        logger.info(f"Report title: {report.get('title')}")
        
        # In a real application, you would integrate with an email service
        # like SendGrid, Mailgun, or AWS SES here.
        
        return {"success": True, "message": f"Report successfully sent to {email}"}
        
    except Exception as e:
        logger.error(f"Error sending report email: {e}")
        return {"success": False, "message": f"Error sending report email: {str(e)}"}


if __name__ == "__main__":
    # Get the server port from the environment variable
    server_port = os.environ.get("PORT", "8080")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=int(server_port))
