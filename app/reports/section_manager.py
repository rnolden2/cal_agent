"""
Section management system for organizing and coordinating report sections.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SectionMetadata:
    """Metadata for a report section"""
    name: str
    title: str
    description: str
    priority: int
    required_agents: List[str]
    dependencies: List[str]
    estimated_tokens: int
    quality_threshold: float

class SectionManager:
    """
    Manages report sections, dependencies, and coordination
    """
    
    def __init__(self):
        # Market research section definitions
        self.market_research_sections = {
            "defense_military_news": SectionMetadata(
                name="defense_military_news",
                title="Defense & Military News Summary",
                description="Provide 2-3 recent news items showing shifts in military strategy, procurement priorities, or modernization goals affecting vehicle power and export power systems.",
                priority=1,
                required_agents=["TrendTracker", "Engineer", "Sales"],
                dependencies=[],
                estimated_tokens=800,
                quality_threshold=0.8
            ),
            "government_solicitations": SectionMetadata(
                name="government_solicitations",
                title="Government & DoD Solicitations",
                description="List active and upcoming solicitations (SBIR/STTR, BAA, RFP) directly supporting the Enercycle inverter family.",
                priority=2,
                required_agents=["TrendTracker", "Engineer", "Sales"],
                dependencies=["defense_military_news"],
                estimated_tokens=1000,
                quality_threshold=0.85
            ),
            "technology_advances": SectionMetadata(
                name="technology_advances",
                title="Technology & Power Electronics Advances",
                description="Highlight 2-3 recent technical developments (e.g., SiC, GaN, thermal solutions) with verified sources.",
                priority=3,
                required_agents=["Engineer", "TrendTracker", "RivalWatcher"],
                dependencies=[],
                estimated_tokens=700,
                quality_threshold=0.8
            ),
            "competitor_updates": SectionMetadata(
                name="competitor_updates",
                title="Defense Contractor & Startup Updates",
                description="Track competitor and potential partner activities in vehicle electrification and export power.",
                priority=4,
                required_agents=["RivalWatcher", "Engineer", "Sales"],
                dependencies=["technology_advances"],
                estimated_tokens=900,
                quality_threshold=0.75
            ),
            "contract_awards": SectionMetadata(
                name="contract_awards",
                title="Contract Awards & Funding News",
                description="Summarize recent DoD awards related to export power and microgrids with verified sources.",
                priority=5,
                required_agents=["TrendTracker", "Sales", "RivalWatcher"],
                dependencies=["government_solicitations"],
                estimated_tokens=600,
                quality_threshold=0.8
            ),
            "vehicle_power_developments": SectionMetadata(
                name="vehicle_power_developments",
                title="Export & Onboard Vehicle Power Developments",
                description="List specific technology adoption or test programs involving bidirectional inverters or high-voltage buses.",
                priority=6,
                required_agents=["Engineer", "TrendTracker", "Sales"],
                dependencies=["technology_advances", "competitor_updates"],
                estimated_tokens=800,
                quality_threshold=0.8
            ),
            "startup_watch": SectionMetadata(
                name="startup_watch",
                title="Emerging Startup Watch",
                description="Identify early-stage startups with SBIR/venture backing in electrification, microgrids, or power electronics.",
                priority=7,
                required_agents=["RivalWatcher", "Engineer", "Sales"],
                dependencies=["competitor_updates"],
                estimated_tokens=500,
                quality_threshold=0.7
            ),
            "commercial_opportunities": SectionMetadata(
                name="commercial_opportunities",
                title="Commercial Application Opportunities",
                description="Identify 3-4 commercial markets where bidirectional inverter technology can be applied.",
                priority=8,
                required_agents=["Sales", "Engineer", "TrendTracker"],
                dependencies=["vehicle_power_developments", "startup_watch"],
                estimated_tokens=1200,
                quality_threshold=0.75
            ),
            "key_takeaways": SectionMetadata(
                name="key_takeaways",
                title="Key Takeaways & Recommendations",
                description="Provide 3-5 bullet points summarizing the most critical strategic actions, risks, or opportunities.",
                priority=9,
                required_agents=["Sales", "Engineer", "TrendTracker", "RivalWatcher"],
                dependencies=["defense_military_news", "government_solicitations", "competitor_updates", "commercial_opportunities"],
                estimated_tokens=600,
                quality_threshold=0.85
            )
        }
    
    def get_section_metadata(self, section_name: str, report_type: str = "market_research") -> Optional[SectionMetadata]:
        """
        Get metadata for a specific section
        """
        if report_type == "market_research":
            return self.market_research_sections.get(section_name)
        return None
    
    def get_all_sections(self, report_type: str = "market_research") -> Dict[str, SectionMetadata]:
        """
        Get all sections for a report type
        """
        if report_type == "market_research":
            return self.market_research_sections
        return {}
    
    def get_section_dependencies(self, section_name: str, report_type: str = "market_research") -> List[str]:
        """
        Get dependencies for a section
        """
        metadata = self.get_section_metadata(section_name, report_type)
        return metadata.dependencies if metadata else []
    
    def get_generation_order(self, report_type: str = "market_research") -> List[str]:
        """
        Get optimal order for section generation based on dependencies and priorities
        """
        sections = self.get_all_sections(report_type)
        
        # Topological sort considering dependencies and priorities
        ordered_sections = []
        remaining_sections = set(sections.keys())
        
        while remaining_sections:
            # Find sections with no unmet dependencies
            ready_sections = []
            for section_name in remaining_sections:
                metadata = sections[section_name]
                unmet_deps = [dep for dep in metadata.dependencies if dep in remaining_sections]
                if not unmet_deps:
                    ready_sections.append((section_name, metadata.priority))
            
            if not ready_sections:
                # Circular dependency or error - add remaining by priority
                ready_sections = [(name, sections[name].priority) for name in remaining_sections]
            
            # Sort by priority and add to order
            ready_sections.sort(key=lambda x: x[1])
            next_section = ready_sections[0][0]
            ordered_sections.append(next_section)
            remaining_sections.remove(next_section)
        
        return ordered_sections
    
    def validate_section_requirements(self, section_name: str, content: str, report_type: str = "market_research") -> Dict[str, Any]:
        """
        Validate that section content meets requirements
        """
        metadata = self.get_section_metadata(section_name, report_type)
        if not metadata:
            return {"valid": False, "errors": ["Unknown section"]}
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }
        
        # Check content length
        content_length = len(content)
        validation_result["metrics"]["content_length"] = content_length
        
        if content_length < 100:
            validation_result["errors"].append("Content too short (minimum 100 characters)")
            validation_result["valid"] = False
        elif content_length < 200:
            validation_result["warnings"].append("Content may be too brief for comprehensive coverage")
        
        # Check for required elements based on section type
        section_requirements = self._get_section_requirements(section_name)
        for requirement in section_requirements:
            if not self._check_requirement(content, requirement):
                validation_result["errors"].append(f"Missing required element: {requirement['description']}")
                validation_result["valid"] = False
        
        # Check for URLs (most sections require verified sources)
        url_count = content.count("http")
        validation_result["metrics"]["url_count"] = url_count
        
        if section_name not in ["key_takeaways"] and url_count == 0:
            validation_result["warnings"].append("No URLs found - consider adding verified sources")
        
        return validation_result
    
    def _get_section_requirements(self, section_name: str) -> List[Dict[str, Any]]:
        """
        Get specific requirements for each section type
        """
        requirements_map = {
            "defense_military_news": [
                {"type": "table_format", "description": "Content should include structured information"},
                {"type": "source_links", "description": "Include verifiable URLs"},
                {"type": "impact_analysis", "description": "Explain relevance to Calnetix products"}
            ],
            "government_solicitations": [
                {"type": "solicitation_details", "description": "Include title, agency, deadline"},
                {"type": "relevance_analysis", "description": "Explain relevance to Enercycle inverter family"},
                {"type": "action_items", "description": "Provide recommended actions"}
            ],
            "technology_advances": [
                {"type": "technical_details", "description": "Include specific technical specifications"},
                {"type": "source_verification", "description": "All claims must have verified sources"},
                {"type": "impact_assessment", "description": "Assess impact on Calnetix technology"}
            ],
            "competitor_updates": [
                {"type": "company_names", "description": "Specific competitor companies mentioned"},
                {"type": "strategic_analysis", "description": "Strategic takeaways provided"},
                {"type": "verified_sources", "description": "All updates have source links"}
            ],
            "contract_awards": [
                {"type": "award_details", "description": "Include recipient, value, scope"},
                {"type": "verified_links", "description": "All awards have announcement links"},
                {"type": "relevance_scope", "description": "Scope relates to export power/microgrids"}
            ],
            "vehicle_power_developments": [
                {"type": "development_details", "description": "Specific technology developments listed"},
                {"type": "source_links", "description": "All developments have source links"},
                {"type": "enercycle_relevance", "description": "Relevance to Enercycle inverter family explained"}
            ],
            "startup_watch": [
                {"type": "startup_details", "description": "Include funding status and focus area"},
                {"type": "opportunity_threat", "description": "Classify as opportunity or threat"},
                {"type": "strategic_notes", "description": "Strategic implications provided"}
            ],
            "commercial_opportunities": [
                {"type": "market_analysis", "description": "Include industry, customers, competitors"},
                {"type": "fit_assessment", "description": "Analyze why it may/may not fit"},
                {"type": "entry_strategy", "description": "Recommend best route to pursue"}
            ],
            "key_takeaways": [
                {"type": "bullet_points", "description": "3-5 bullet points provided"},
                {"type": "strategic_focus", "description": "Focus on strategic actions and opportunities"},
                {"type": "actionable_items", "description": "Recommendations are actionable"}
            ]
        }
        
        return requirements_map.get(section_name, [])
    
    def _check_requirement(self, content: str, requirement: Dict[str, Any]) -> bool:
        """
        Check if content meets a specific requirement
        """
        req_type = requirement["type"]
        content_lower = content.lower()
        
        # Basic requirement checks
        if req_type == "table_format":
            return "|" in content or ":" in content  # Simple table indicators
        elif req_type == "source_links":
            return "http" in content
        elif req_type == "impact_analysis":
            return any(word in content_lower for word in ["impact", "relevance", "calnetix", "enercycle"])
        elif req_type == "solicitation_details":
            return any(word in content_lower for word in ["sbir", "sttr", "baa", "rfp", "deadline"])
        elif req_type == "relevance_analysis":
            return "enercycle" in content_lower or "inverter" in content_lower
        elif req_type == "action_items":
            return any(word in content_lower for word in ["recommend", "propose", "action", "should"])
        elif req_type == "technical_details":
            return any(word in content_lower for word in ["sic", "gan", "thermal", "power", "voltage"])
        elif req_type == "source_verification":
            return "http" in content and len(content.split("http")) > 1
        elif req_type == "impact_assessment":
            return any(word in content_lower for word in ["benefit", "challenge", "impact", "advantage"])
        elif req_type == "company_names":
            # Check for capitalized company names
            import re
            return bool(re.search(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', content))
        elif req_type == "strategic_analysis":
            return any(word in content_lower for word in ["strategic", "competitive", "market", "opportunity"])
        elif req_type == "verified_sources":
            return "http" in content
        elif req_type == "award_details":
            return any(word in content_lower for word in ["award", "contract", "recipient", "value"])
        elif req_type == "verified_links":
            return "http" in content
        elif req_type == "relevance_scope":
            return any(word in content_lower for word in ["power", "microgrid", "export", "inverter"])
        elif req_type == "development_details":
            return any(word in content_lower for word in ["development", "test", "program", "technology"])
        elif req_type == "enercycle_relevance":
            return "enercycle" in content_lower or "inverter" in content_lower
        elif req_type == "startup_details":
            return any(word in content_lower for word in ["funding", "sbir", "series", "venture"])
        elif req_type == "opportunity_threat":
            return any(word in content_lower for word in ["opportunity", "threat", "partner", "competitor"])
        elif req_type == "strategic_notes":
            return any(word in content_lower for word in ["strategic", "implication", "note"])
        elif req_type == "market_analysis":
            return any(word in content_lower for word in ["market", "industry", "customer", "competitor"])
        elif req_type == "fit_assessment":
            return any(word in content_lower for word in ["fit", "match", "suitable", "appropriate"])
        elif req_type == "entry_strategy":
            return any(word in content_lower for word in ["strategy", "approach", "route", "pursue"])
        elif req_type == "bullet_points":
            return content.count("•") >= 3 or content.count("-") >= 3 or content.count("*") >= 3
        elif req_type == "strategic_focus":
            return any(word in content_lower for word in ["strategic", "action", "risk", "opportunity"])
        elif req_type == "actionable_items":
            return any(word in content_lower for word in ["action", "recommend", "should", "implement"])
        
        return True  # Default to true for unknown requirements
    
    def get_section_template(self, section_name: str, report_type: str = "market_research") -> str:
        """
        Get template structure for a section
        """
        templates = {
            "defense_military_news": """
| Headline / Summary | Impact / Relevance |
|-------------------|-------------------|
| Headline: [Insert article title]<br>Source & Date: [e.g., Defense News, MM/DD/YYYY] | [Explain how this news item impacts demand or standards for Calnetix products] |
| Headline: [Insert article title]<br>Source & Date: [e.g., Army.mil, MM/DD/YYYY] | [Explain relevance to microgrid interoperability, export power integration, or Army modernization] |
""",
            "government_solicitations": """
| Solicitation | Agency | Deadline | Relevance / Recommended Action |
|-------------|--------|----------|-------------------------------|
| Title: [e.g., SBIR A244-072: Lighter, Low-Cost Bidirectional Inverters]<br>Topic Code: A244-072 | Army | [MM/DD/YYYY] | [Detailed relevance and recommended action] |
""",
            "technology_advances": """
| Update | Source & Date | Potential Impact |
|--------|---------------|------------------|
| Development: [e.g., New wide-bandgap SiC MOSFET]<br>Details: [Briefly describe key specs] | [IEEE Spectrum, MM/YYYY] | [Explain how this could increase power density or efficiency] |
""",
            "competitor_updates": """
| Company | Update (with link) | Strategic Takeaway |
|---------|-------------------|-------------------|
| [Company Name]<br>Update: [Summarize demo, announcement, acquisition] | [Link to source] | [Implications for market positioning or partnership] |
""",
            "contract_awards": """
| Award (with link) | Recipient | Value | Scope Summary |
|------------------|-----------|-------|---------------|
| [Award Title]<br>Date: [MM/DD/YYYY] | [Company or organization] | [$XX M] | [Scope description: e.g., prototype onboard power systems] |
""",
            "vehicle_power_developments": """
| Development (with link) | Source & Date | Relevance to Enercycle inverter family |
|------------------------|---------------|-------------------------------------|
| [e.g., Oshkosh hybrid drive test] | [Defense News, MM/YYYY] | [How this informs integration requirements] |
""",
            "startup_watch": """
| Startup | Focus Area | Funding Status | Opportunity / Threat |
|---------|------------|----------------|---------------------|
| [Startup Name] | [e.g., mobile microgrids] | [e.g., SBIR Phase I] | [Opportunity: potential partner / Threat: competitor] |
""",
            "commercial_opportunities": """
| Industry / Market | Potential Customers | Current Competitors | Why It May Fit | Why It May Be a Bad Fit | Best Route to Pursue |
|------------------|-------------------|-------------------|----------------|----------------------|-------------------|
| [Industry Name] | [Customer segments] | [Competitor names] | [Fit rationale] | [Fit risks] | [Entry strategy] |
""",
            "key_takeaways": """
• [Action]: [Description]
• [Action]: [Description]
• [Action]: [Description]
• [Risk/Opportunity]: [Description]
• [Strategic Recommendation]: [Description]
"""
        }
        
        return templates.get(section_name, "")
    
    def estimate_section_complexity(self, section_name: str, report_type: str = "market_research") -> Dict[str, Any]:
        """
        Estimate complexity and resource requirements for a section
        """
        metadata = self.get_section_metadata(section_name, report_type)
        if not metadata:
            return {"complexity": "unknown"}
        
        # Base complexity on multiple factors
        complexity_factors = {
            "agent_count": len(metadata.required_agents),
            "dependency_count": len(metadata.dependencies),
            "estimated_tokens": metadata.estimated_tokens,
            "quality_threshold": metadata.quality_threshold
        }
        
        # Calculate complexity score
        complexity_score = (
            complexity_factors["agent_count"] * 0.3 +
            complexity_factors["dependency_count"] * 0.2 +
            (complexity_factors["estimated_tokens"] / 1000) * 0.3 +
            complexity_factors["quality_threshold"] * 0.2
        )
        
        if complexity_score < 1.5:
            complexity_level = "low"
        elif complexity_score < 2.5:
            complexity_level = "medium"
        else:
            complexity_level = "high"
        
        return {
            "complexity": complexity_level,
            "score": complexity_score,
            "factors": complexity_factors,
            "estimated_time_minutes": int(complexity_score * 5),  # Rough estimate
            "recommended_agents": metadata.required_agents
        }
