"""
CAL - Collaborative AI Layer
"""

import logging
import os
from typing import List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Query, Request, UploadFile, File, Form, HTTPException
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
from .storage.document_repository import DocumentRepository
from .utils.document_processor import DocumentProcessor
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


# Document Repository Upload Endpoints

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    description: Optional[str] = Form(None)
):
    """
    Upload a reference document for processing and indexing.
    
    Args:
        file: The uploaded txt file
        user_id: User ID who is uploading the document
        description: Optional description of the reference document
        
    Returns:
        Upload result with document ID and processing status
    """
    try:
        document_repository = DocumentRepository()
        
        if not document_repository.is_available():
            raise HTTPException(status_code=503, detail="Document repository service unavailable")
        
        # Read file content
        file_content = await file.read()
        filename = file.filename or "document.txt"
        
        # Upload to document repository
        upload_result = await document_repository.upload_document(
            file_content=file_content,
            filename=filename,
            user_id=user_id,
            metadata={"description": description} if description else None
        )
        
        if upload_result["success"]:
            # Trigger background processing
            processor = DocumentProcessor()
            processing_result = await processor.process_document(upload_result["document_id"])
            
            return {
                "success": True,
                "message": "Document uploaded and processed successfully",
                "document_id": upload_result["document_id"],
                "stored_filename": upload_result["stored_filename"],
                "processing_result": processing_result
            }
        else:
            raise HTTPException(status_code=400, detail=upload_result["error"])
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/documents")
async def list_documents(
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, le=100)
):
    """
    List uploaded reference documents.
    
    Args:
        user_id: Optional user ID filter
        limit: Maximum number of documents to return
        
    Returns:
        List of uploaded reference documents
    """
    try:
        document_repository = DocumentRepository()
        
        if not document_repository.is_available():
            return {"documents": [], "message": "Document repository service unavailable"}
        
        documents = await document_repository.list_documents(user_id=user_id, limit=limit)
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return {"success": False, "error": str(e), "documents": []}


@app.get("/feedback/files/{file_id}")
async def get_feedback_file(file_id: str):
    """
    Get a specific feedback file by ID.
    
    Args:
        file_id: The file ID to retrieve
        
    Returns:
        File information and content
    """
    try:
        cloud_storage = FeedbackCloudStorage()
        
        if not cloud_storage.is_available():
            raise HTTPException(status_code=503, detail="Cloud storage service unavailable")
        
        file_info = await cloud_storage.get_feedback_file(file_id)
        
        if file_info:
            return {
                "success": True,
                "file_info": file_info
            }
        else:
            raise HTTPException(status_code=404, detail="File not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/feedback/files/{file_id}")
async def delete_feedback_file(file_id: str):
    """
    Delete a feedback file by ID.
    
    Args:
        file_id: The file ID to delete
        
    Returns:
        Deletion result
    """
    try:
        cloud_storage = FeedbackCloudStorage()
        
        if not cloud_storage.is_available():
            raise HTTPException(status_code=503, detail="Cloud storage service unavailable")
        
        success = await cloud_storage.delete_feedback_file(file_id)
        
        if success:
            return {
                "success": True,
                "message": "File deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="File not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback/files/{file_id}/process")
async def process_feedback_file(file_id: str):
    """
    Manually trigger processing of a feedback file.
    
    Args:
        file_id: The file ID to process
        
    Returns:
        Processing result
    """
    try:
        processor = FeedbackFileProcessor()
        result = await processor.process_feedback_file(file_id)
        
        return {
            "success": result["success"],
            "message": "Processing completed" if result["success"] else result.get("error", "Processing failed"),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error processing feedback file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedback/files/processed")
async def list_processed_feedback_files():
    """
    List all processed feedback files.
    
    Returns:
        List of processed files with metadata
    """
    try:
        cloud_storage = FeedbackCloudStorage()
        
        if not cloud_storage.is_available():
            return {"files": [], "message": "Cloud storage service unavailable"}
        
        files = await cloud_storage.list_processed_files()
        
        return {
            "success": True,
            "processed_files": files,
            "count": len(files)
        }
        
    except Exception as e:
        logger.error(f"Error listing processed feedback files: {e}")
        return {"success": False, "error": str(e), "processed_files": []}


@app.get("/feedback/pipeline/validate")
async def validate_feedback_pipeline():
    """
    Validate the feedback processing pipeline.
    
    Returns:
        Pipeline validation results
    """
    try:
        processor = FeedbackFileProcessor()
        validation_result = await processor.validate_processing_pipeline()
        
        return {
            "success": True,
            "validation": validation_result
        }
        
    except Exception as e:
        logger.error(f"Error validating feedback pipeline: {e}")
        return {"success": False, "error": str(e)}


@app.post("/feedback/pipeline/process-pending")
async def process_pending_feedback_files():
    """
    Automatically process any pending feedback files.
    This is the automatic processing trigger for uploaded files.
    
    Returns:
        Processing results for all pending files
    """
    try:
        cloud_storage = FeedbackCloudStorage()
        processor = FeedbackFileProcessor()
        
        if not cloud_storage.is_available():
            return {"success": False, "error": "Cloud storage service unavailable"}
        
        # Get validation to find pending files
        validation = await processor.validate_processing_pipeline()
        pending_files = validation.get("pending_files", [])
        
        if not pending_files:
            return {
                "success": True,
                "message": "No pending files to process",
                "processed_count": 0,
                "results": []
            }
        
        # Process pending files
        file_ids = [f["file_id"] for f in pending_files]
        results = await processor.batch_process_files(file_ids)
        
        processed_count = sum(1 for r in results if r.get("success"))
        failed_count = len(results) - processed_count
        
        return {
            "success": True,
            "message": f"Processing complete: {processed_count} successful, {failed_count} failed",
            "processed_count": processed_count,
            "failed_count": failed_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing pending feedback files: {e}")
        return {"success": False, "error": str(e)}


@app.get("/feedback/pipeline/status")
async def get_feedback_pipeline_status():
    """
    Get comprehensive status of the feedback processing pipeline.
    
    Returns:
        Complete pipeline status including files, processing stats, and health
    """
    try:
        cloud_storage = FeedbackCloudStorage()
        processor = FeedbackFileProcessor()
        
        if not cloud_storage.is_available():
            return {
                "success": False,
                "error": "Cloud storage service unavailable",
                "status": "offline"
            }
        
        # Get comprehensive validation data
        validation = await processor.validate_processing_pipeline()
        
        # Get file lists
        uploaded_files = await cloud_storage.list_feedback_files()
        processed_files = await cloud_storage.list_processed_files()
        
        # Calculate health metrics
        total_uploaded = len(uploaded_files)
        total_processed = len(processed_files)
        pending_count = validation.get("pending_processing_count", 0)
        
        processing_rate = (total_processed / total_uploaded * 100) if total_uploaded > 0 else 0
        
        status = {
            "success": True,
            "status": "healthy" if processing_rate > 80 else "warning" if processing_rate > 50 else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            
            "file_counts": {
                "uploaded_files": total_uploaded,
                "processed_files": total_processed,
                "pending_processing": pending_count,
                "processing_rate_percentage": round(processing_rate, 2)
            },
            
            "feedback_statistics": {
                "total_feedback_entries": validation.get("total_feedback_entries", 0),
                "categories_distribution": validation.get("categories_distribution", {}),
            },
            
            "recent_activity": {
                "recent_uploads": [f for f in uploaded_files[:5]],  # Last 5 uploads
                "recent_processed": [f for f in processed_files[:5]]  # Last 5 processed
            },
            
            "system_health": {
                "cloud_storage_available": cloud_storage.is_available(),
                "processing_pipeline_functional": True,
                "feedback_integration_active": True
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting feedback pipeline status: {e}")
        return {
            "success": False,
            "error": str(e),
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }


@app.post("/feedback/pipeline/test")
async def test_feedback_pipeline():
    """
    Test the complete feedback pipeline with a sample file.
    
    Returns:
        Test results showing pipeline functionality
    """
    try:
        cloud_storage = FeedbackCloudStorage()
        processor = FeedbackFileProcessor()
        
        if not cloud_storage.is_available():
            return {"success": False, "error": "Cloud storage service unavailable"}
        
        # Create test feedback content
        test_content = """
Test Feedback for Pipeline Validation

1. Presentation Feedback:
The presentation was too verbose and could be more concise. Focus on key points and reduce technical jargon when speaking to business audiences.

2. Technical Accuracy:
Ensure all technical specifications are verified and include proper sources. Double-check calculations and measurements before presenting.

3. Business Focus:
Need to emphasize the business value and ROI more clearly. Connect technical features to customer benefits and revenue opportunities.
        """.strip()
        
        test_filename = f"test_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Upload test file
        upload_result = await cloud_storage.upload_feedback_file(
            file_content=test_content.encode('utf-8'),
            filename=test_filename,
            user_id="pipeline_test",
            metadata={"test": True, "pipeline_validation": True}
        )
        
        if not upload_result["success"]:
            return {
                "success": False,
                "error": f"Test file upload failed: {upload_result['error']}",
                "stage": "upload"
            }
        
        # Process test file
        file_id = upload_result["file_id"]
        processing_result = await processor.process_feedback_file(file_id)
        
        if not processing_result["success"]:
            return {
                "success": False,
                "error": f"Test file processing failed: {processing_result['error']}",
                "stage": "processing",
                "file_id": file_id
            }
        
        # Verify processed file exists
        processed_files = await cloud_storage.list_processed_files()
        test_processed = any(f.get("original_file_id") == file_id for f in processed_files)
        
        # Clean up test file
        cleanup_success = await cloud_storage.delete_feedback_file(file_id)
        
        return {
            "success": True,
            "message": "Pipeline test completed successfully",
            "test_results": {
                "upload_successful": True,
                "processing_successful": True,
                "processed_file_created": test_processed,
                "sections_processed": processing_result.get("sections_count", 0),
                "dominant_category": processing_result.get("dominant_category", "unknown"),
                "file_tags": processing_result.get("file_tags", []),
                "cleanup_successful": cleanup_success
            },
            "file_id": file_id,
            "test_filename": test_filename
        }
        
    except Exception as e:
        logger.error(f"Error testing feedback pipeline: {e}")
        return {
            "success": False,
            "error": str(e),
            "stage": "unknown"
        }


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
