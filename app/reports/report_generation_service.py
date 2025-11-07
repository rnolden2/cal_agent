"""
Service for generating report sections using AI agents.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from ..agent_schema.agent_master_schema import AgentCallModel, ReportGenerationRequest
from ..orchestrator.agent_orchestrator import AgentOrchestrator
from ..context.context_injector import ContextInjector

logger = logging.getLogger(__name__)


def select_provider_for_section(section_title: str, custom_map: Dict[str, str]) -> str:
    """
    Select the appropriate LLM provider for a given section based on content type.
    
    Args:
        section_title: The title of the section
        custom_map: User-provided custom mapping of section to provider
        
    Returns:
        Provider name (e.g., 'perplexity', 'google', 'openai', 'xai')
    """
    # Check custom map first
    if section_title in custom_map:
        return custom_map[section_title]

    # Default assignments based on content type
    research_sections = [
        "Defense & Military News Summary",
        "Government & DoD Solicitations",
        "Contract Awards & Funding News",
        "Emerging Startup Watch",
    ]
    technical_sections = [
        "Technology & Power Electronics Advances",
        "Export & Onboard Vehicle Power Developments",
    ]

    if section_title in research_sections:
        return "perplexity"
    elif section_title in technical_sections:
        return "google"
    else:
        # Alternate between OpenAI and XAI for general sections
        return "openai" if hash(section_title) % 2 == 0 else "xai"


async def generate_section(
    section,
    orchestrator: AgentOrchestrator,
    report_req: ReportGenerationRequest,
    app_state: Any,
    section_cache: Dict[str, Any]
) -> Any:
    """
    Generate content for a single report section.
    
    Args:
        section: The ReportSection object to generate content for
        orchestrator: AgentOrchestrator instance
        report_req: The report generation request
        app_state: Application state containing templates
        section_cache: Cache for section responses
        
    Returns:
        The updated section with generated content
    """
    # Generate the prompt using context injector
    section_prompt = ContextInjector().market_report_context(
        title=section.title,
        description=report_req.description,
        market_research_template=app_state.market_research_template,
    )

    # Generate cache key
    cache_key = f"{section.title}_{hash(section_prompt)}"

    if cache_key in section_cache:
        logger.info(f"Cache hit for section: {section.title}")
        orchestrator_response = section_cache[cache_key]
    else:
        provider = select_provider_for_section(
            section.title, report_req.custom_llm_map
        )

        agent_request = AgentCallModel(
            provider=provider,
            model=1,
            response=section_prompt,
            additional_context=f"Market research report generation for section: {section.title}",
            user_id=report_req.user_id,
            topic_id=None,
            enable_verification=report_req.enable_verification,
        )

        orchestrator_response = await orchestrator.process_request(agent_request)
        section_cache[cache_key] = orchestrator_response
        logger.info(
            f"Cache miss - generated and cached for section: {section.title}"
        )

    section.content = orchestrator_response.get(
        "response", f"Content for {section.title} section"
    )
    section.status = "completed"
    section.agent_contributors = orchestrator_response.get(
        "agents_involved", ["General"]
    )
    section.last_updated = datetime.now()

    return section


async def bounded_generate_section(
    section,
    semaphore,
    orchestrator: AgentOrchestrator,
    report_req: ReportGenerationRequest,
    app_state: Any,
    section_cache: Dict[str, Any]
) -> Any:
    """
    Generate a section with concurrency limiting via semaphore.
    
    Args:
        section: The ReportSection to generate
        semaphore: asyncio.Semaphore for concurrency control
        orchestrator: AgentOrchestrator instance
        report_req: The report generation request
        app_state: Application state
        section_cache: Cache for section responses
        
    Returns:
        The updated section
    """
    async with semaphore:
        try:
            return await generate_section(
                section, orchestrator, report_req, app_state, section_cache
            )
        except Exception as e:
            logger.error(
                f"Error in bounded_generate_section for {getattr(section, 'title', 'unknown')}: {e}"
            )
            section.content = f"Error generating content: {str(e)}"
            section.status = "error"
            return section
