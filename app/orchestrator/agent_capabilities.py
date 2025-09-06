"""
Defines the capabilities and collaboration mappings for each agent.
"""

from typing import Dict, List, Any

AGENT_CAPABILITIES = {
    "CustomerConnect": {
        "domains": ["communication", "email", "professional_writing", "customer_engagement"],
        "feedback_categories": ["presentation_skills", "communication_style"],
        "collaboration_with": ["Editor", "ProfessionalMentor"],
        "fact_verification": False,
        "description": "Customer Engagement Agent for professional communications"
    },
    "TrendTracker": {
        "domains": ["market_research", "industry_trends", "competitive_analysis", "military_tech"],
        "feedback_categories": ["market_analysis", "research_depth", "technical_accuracy"],
        "collaboration_with": ["RivalWatcher", "Sales", "Engineer"],
        "fact_verification": True,
        "description": "Market Research Agent for trends and opportunities"
    },
    "RivalWatcher": {
        "domains": ["competitor_intelligence", "market_analysis", "strategic_planning"],
        "feedback_categories": ["competitive_analysis", "research_depth"],
        "collaboration_with": ["TrendTracker", "Sales", "Engineer"],
        "fact_verification": True,
        "description": "Competitor Intelligence Agent for strategic insights"
    },
    "Engineer": {
        "domains": ["technical_analysis", "engineering_concepts", "system_design"],
        "feedback_categories": ["technical_accuracy", "engineering_depth"],
        "collaboration_with": ["TrendTracker", "RivalWatcher", "TechWiz"],
        "fact_verification": True,
        "description": "Engineering Agent for technical guidance and analysis"
    },
    "Sales": {
        "domains": ["business_strategy", "sales_tactics", "government_sales"],
        "feedback_categories": ["business_focus", "sales_strategy"],
        "collaboration_with": ["TrendTracker", "RivalWatcher", "CustomerConnect"],
        "fact_verification": False,
        "description": "Sales Agent for business strategy and opportunities"
    },
    "Editor": {
        "domains": ["content_editing", "writing_improvement", "clarity"],
        "feedback_categories": ["presentation_skills", "communication_style"],
        "collaboration_with": ["CustomerConnect", "TechWiz", "DocumentMaster"],
        "fact_verification": False,
        "description": "Editor Agent for content refinement and clarity"
    },
    "TechWiz": {
        "domains": ["technical_writing", "documentation", "content_creation"],
        "feedback_categories": ["technical_accuracy", "presentation_skills"],
        "collaboration_with": ["Engineer", "Editor", "DocumentMaster"],
        "fact_verification": False,
        "description": "Technical Writing Agent for documentation and content"
    },
    "DocumentMaster": {
        "domains": ["document_management", "information_retrieval", "organization"],
        "feedback_categories": ["information_accuracy", "organization"],
        "collaboration_with": ["Editor", "TechWiz"],
        "fact_verification": False,
        "description": "Document Management Agent for information organization"
    },
    "ProfessionalMentor": {
        "domains": ["professional_development", "coaching", "performance_improvement"],
        "feedback_categories": ["presentation_skills", "business_focus", "professional_growth"],
        "collaboration_with": ["CustomerConnect", "Sales"],
        "fact_verification": False,
        "description": "Professional Mentor Agent for career development"
    },
    "General": {
        "domains": ["general_assistance", "basic_tasks"],
        "feedback_categories": ["general_feedback"],
        "collaboration_with": [],
        "fact_verification": False,
        "description": "General Assistant Agent for basic tasks"
    }
}

FEEDBACK_CATEGORIES = {
    "presentation_skills": [
        "tone_and_cadence", "presentation_mode", "technical_familiarity",
        "connection_to_needs", "over_communication", "clarity", "engagement"
    ],
    "technical_accuracy": [
        "company_claims", "technology_explanation", "requirements_clarity",
        "implementation_details", "testing_standards", "fact_verification"
    ],
    "business_focus": [
        "customer_needs", "business_opportunity", "market_analysis",
        "competitive_positioning", "revenue_focus", "strategic_thinking"
    ],
    "communication_style": [
        "professional_tone", "audience_awareness", "message_clarity",
        "persuasiveness", "conciseness"
    ],
    "research_depth": [
        "source_quality", "data_accuracy", "comprehensive_analysis",
        "trend_identification", "market_insights"
    ]
}

TASK_TYPE_MAPPING = {
    "market_research": ["TrendTracker", "RivalWatcher", "Engineer", "Sales"],
    "competitor_analysis": ["RivalWatcher", "TrendTracker", "Sales"],
    "technical_analysis": ["Engineer", "TechWiz", "TrendTracker"],
    "business_strategy": ["Sales", "TrendTracker", "RivalWatcher"],
    "customer_communication": ["CustomerConnect", "Editor", "ProfessionalMentor"],
    "document_creation": ["TechWiz", "Editor", "DocumentMaster"],
    "professional_development": ["ProfessionalMentor", "Sales", "CustomerConnect"],
    "general": ["General"]
}

def get_agents_for_task(task_type: str) -> List[str]:
    """
    Get recommended agents for a specific task type
    """
    return TASK_TYPE_MAPPING.get(task_type, ["General"])

def get_agent_capabilities(agent_name: str) -> Dict[str, Any]:
    """
    Get capabilities for a specific agent
    """
    return AGENT_CAPABILITIES.get(agent_name, {})

def get_collaboration_agents(agent_name: str) -> List[str]:
    """
    Get agents that can collaborate with the specified agent
    """
    capabilities = get_agent_capabilities(agent_name)
    return capabilities.get("collaboration_with", [])

def requires_fact_verification(agent_name: str) -> bool:
    """
    Check if an agent requires fact verification
    """
    capabilities = get_agent_capabilities(agent_name)
    return capabilities.get("fact_verification", False)

def get_feedback_categories_for_agent(agent_name: str) -> List[str]:
    """
    Get relevant feedback categories for an agent
    """
    capabilities = get_agent_capabilities(agent_name)
    return capabilities.get("feedback_categories", [])
