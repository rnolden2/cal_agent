"""
Collaborative report generation system coordinating multiple agents for fact-verified reports.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass

from ..orchestrator.agent_orchestrator import AgentOrchestrator
from ..verification.quality_assurance import QualityAssuranceSystem
from ..agent_schema.agent_master_schema import AgentCallModel, Provider, AgentContribution
from .section_manager import SectionManager
from .template_processor import TemplateProcessor

logger = logging.getLogger(__name__)

@dataclass
class ReportRequest:
    """Request for collaborative report generation"""
    report_type: str
    user_id: str
    template_name: str
    parameters: Dict[str, Any]
    verification_required: bool = True
    quality_threshold: float = 0.75
    topic_id: Optional[str] = None

@dataclass
class VerifiedReport:
    """Complete verified report with all sections"""
    report_id: str
    report_type: str
    content: str
    sections: Dict[str, Dict[str, Any]]
    overall_quality_score: float
    verification_status: str
    agents_involved: List[str]
    generation_timestamp: datetime
    quality_metrics: Dict[str, Any]
    recommendations: List[str]

class CollaborativeReportGenerator:
    """
    Coordinates multiple agents for fact-verified report generation
    """
    
    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.quality_assurance = QualityAssuranceSystem()
        self.section_manager = SectionManager()
        self.template_processor = TemplateProcessor()
        
        # Report section assignments based on market_research.txt template
        self.report_section_agents = {
            "defense_military_news": {
                "primary": "TrendTracker",
                "verification": "Engineer",
                "business_analysis": "Sales"
            },
            "government_solicitations": {
                "primary": "TrendTracker", 
                "technical_review": "Engineer",
                "business_opportunity": "Sales"
            },
            "technology_advances": {
                "primary": "Engineer",
                "market_impact": "TrendTracker",
                "competitive_analysis": "RivalWatcher"
            },
            "competitor_updates": {
                "primary": "RivalWatcher",
                "technical_assessment": "Engineer",
                "strategic_implications": "Sales"
            },
            "contract_awards": {
                "primary": "TrendTracker",
                "business_analysis": "Sales",
                "competitive_impact": "RivalWatcher"
            },
            "vehicle_power_developments": {
                "primary": "Engineer",
                "market_analysis": "TrendTracker",
                "business_opportunity": "Sales"
            },
            "startup_watch": {
                "primary": "RivalWatcher",
                "technical_assessment": "Engineer",
                "partnership_analysis": "Sales"
            },
            "commercial_opportunities": {
                "primary": "Sales",
                "technical_feasibility": "Engineer",
                "market_research": "TrendTracker"
            },
            "key_takeaways": {
                "primary": "Sales",
                "technical_input": "Engineer",
                "market_insights": "TrendTracker",
                "competitive_intelligence": "RivalWatcher"
            }
        }
        
        # Section priorities for collaborative generation
        self.section_priorities = {
            "defense_military_news": 1,
            "government_solicitations": 2,
            "technology_advances": 3,
            "competitor_updates": 4,
            "contract_awards": 5,
            "vehicle_power_developments": 6,
            "startup_watch": 7,
            "commercial_opportunities": 8,
            "key_takeaways": 9
        }
    
    async def generate_market_research(self, request: ReportRequest) -> VerifiedReport:
        """
        Generate comprehensive market research report with fact verification
        """
        try:
            logger.info(f"Starting collaborative market research generation for user {request.user_id}")
            
            # 1. Initialize report structure
            report_id = self._generate_report_id()
            report_sections = {}
            all_agents_involved = set()
            
            # 2. Process template and extract section requirements
            template_sections = self.template_processor.parse_market_research_template()
            
            # 3. Generate each section collaboratively
            for section_name, section_config in template_sections.items():
                if section_name in self.report_section_agents:
                    logger.info(f"Generating section: {section_name}")
                    
                    section_result = await self._generate_section_collaboratively(
                        section_name=section_name,
                        section_config=section_config,
                        request=request,
                        report_id=report_id
                    )
                    
                    report_sections[section_name] = section_result
                    all_agents_involved.update(section_result.get("agents_involved", []))
            
            # 4. Compile complete report
            complete_report = self._compile_report_sections(report_sections, template_sections)
            
            # 5. Perform overall quality assurance
            overall_quality_assessment = await self.quality_assurance.assess_content_quality(
                content=complete_report,
                context=f"Market Research Report - {report_id}"
            )
            
            # 6. Generate final recommendations
            final_recommendations = self._generate_report_recommendations(
                report_sections, overall_quality_assessment
            )
            
            # 7. Create verified report
            verified_report = VerifiedReport(
                report_id=report_id,
                report_type=request.report_type,
                content=complete_report,
                sections=report_sections,
                overall_quality_score=overall_quality_assessment.overall_quality_score,
                verification_status=overall_quality_assessment.approval_status,
                agents_involved=list(all_agents_involved),
                generation_timestamp=datetime.now(),
                quality_metrics=overall_quality_assessment.quality_metrics,
                recommendations=final_recommendations
            )
            
            logger.info(f"Market research report {report_id} completed with quality score: {overall_quality_assessment.overall_quality_score:.2f}")
            
            return verified_report
            
        except Exception as e:
            logger.error(f"Error generating market research report: {e}")
            raise
    
    async def _generate_section_collaboratively(self, 
                                              section_name: str,
                                              section_config: Dict[str, Any],
                                              request: ReportRequest,
                                              report_id: str) -> Dict[str, Any]:
        """
        Generate a single report section using collaborative agents with new storage structure
        """
        try:
            # Get agent assignments for this section
            agent_assignments = self.report_section_agents.get(section_name, {})
            
            # Store individual agent contributions
            agent_contributions = []
            agents_involved = []
            
            for role, agent_name in agent_assignments.items():
                # Create specialized prompt for this agent's role in the section
                agent_prompt = self._create_section_prompt(
                    section_name=section_name,
                    agent_role=role,
                    agent_name=agent_name,
                    section_config=section_config,
                    request_parameters=request.parameters
                )
                
                # Create agent request
                provider = self._determine_optimal_provider(agent_name)
                agent_request = AgentCallModel(
                    provider=provider,
                    model=1,  # Use complex model for report generation
                    response=agent_prompt,
                    user_id=request.user_id,
                    topic_id=f"{report_id}_{section_name}_{role}",
                    additional_context=f"Report Section: {section_name}, Role: {role}"
                )
                
                # Process through orchestrator for full verification
                agent_response = await self.orchestrator.process_request(agent_request)
                
                # Create AgentContribution object
                content = agent_response.get("response", "")
                contribution = AgentContribution(
                    agent_name=agent_name,
                    agent_role=role,
                    content=content,
                    quality_score=agent_response.get("quality_score", 0.0),
                    verification_status="verified" if agent_response.get("verification_results", {}).get("approved", False) else "unverified",
                    timestamp=datetime.now(),
                    llm_provider=provider.value,
                    llm_model=agent_response.get("model_used", "unknown"),
                    word_count=len(content.split()),
                    token_count=len(content) // 4,  # Rough estimate
                    feedback_applied=agent_response.get("feedback_applied", [])
                )
                
                agent_contributions.append(contribution)
                agents_involved.extend(agent_response.get("agents_involved", []))
            
            # Synthesize section responses using new method
            synthesized_content = self._synthesize_contributions(
                agent_contributions=agent_contributions,
                section_name=section_name,
                synthesis_method="smart_merge"
            )
            
            # Perform section-level quality check
            section_quality = await self.quality_assurance.assess_content_quality(
                content=synthesized_content,
                context=f"Report Section: {section_name}"
            )
            
            # Calculate quality metrics from contributions
            quality_metrics = {
                "average_quality_score": sum(c.quality_score for c in agent_contributions) / len(agent_contributions) if agent_contributions else 0.0,
                "verified_contributions": sum(1 for c in agent_contributions if c.verification_status == "verified"),
                "total_contributions": len(agent_contributions),
                "total_word_count": sum(c.word_count for c in agent_contributions)
            }
            
            return {
                "agent_contributions": agent_contributions,
                "synthesized_content": synthesized_content,
                "synthesis_method": "smart_merge",
                "agents_involved": list(set(agents_involved)),
                "quality_assessment": section_quality,
                "quality_metrics": quality_metrics,
                "section_config": section_config
            }
            
        except Exception as e:
            logger.error(f"Error generating section {section_name}: {e}")
            return {
                "agent_contributions": [],
                "synthesized_content": f"Error generating section {section_name}: {str(e)}",
                "synthesis_method": "error",
                "agents_involved": [],
                "quality_assessment": None,
                "quality_metrics": {},
                "section_config": section_config
            }
    
    def _create_section_prompt(self, 
                             section_name: str,
                             agent_role: str,
                             agent_name: str,
                             section_config: Dict[str, Any],
                             request_parameters: Dict[str, Any]) -> str:
        """
        Create specialized prompt for agent's role in report section
        """
        base_context = f"""
You are contributing to a comprehensive market research report section: "{section_name}".
Your role in this section is: {agent_role}.

Section Requirements:
{section_config.get('description', 'Generate relevant content for this section')}

CRITICAL REQUIREMENTS:
- Include ONLY information with verifiable sources and working URLs
- Do NOT fabricate links or make unverified claims
- Focus on defense/military applications and power electronics
- Ensure all dates, companies, and technical specifications are accurate
- Provide specific, actionable insights relevant to Calnetix products

"""
        
        # Role-specific instructions
        role_instructions = {
            "primary": f"""
As the PRIMARY contributor, provide the main content for this section including:
- Key findings and developments
- Specific examples with verified sources
- Quantitative data where available
- Direct relevance to Calnetix Enercycle inverter family
""",
            "verification": f"""
As the VERIFICATION specialist, ensure:
- All technical claims are accurate and verifiable
- Sources are credible and accessible
- Technical specifications are correct
- Claims align with industry standards
""",
            "business_analysis": f"""
As the BUSINESS ANALYST, focus on:
- Market opportunities and threats
- Competitive implications
- Revenue potential and business impact
- Strategic recommendations
""",
            "technical_review": f"""
As the TECHNICAL REVIEWER, evaluate:
- Technical feasibility and requirements
- Engineering implications
- Technology trends and innovations
- Integration challenges and solutions
""",
            "market_impact": f"""
As the MARKET IMPACT analyst, assess:
- Market size and growth potential
- Industry adoption trends
- Customer demand indicators
- Market positioning implications
""",
            "competitive_analysis": f"""
As the COMPETITIVE ANALYST, examine:
- Competitor activities and announcements
- Market positioning changes
- Competitive advantages and threats
- Partnership and acquisition opportunities
""",
            "strategic_implications": f"""
As the STRATEGIC ADVISOR, provide:
- Long-term strategic recommendations
- Risk assessment and mitigation
- Partnership and collaboration opportunities
- Market entry and expansion strategies
"""
        }
        
        role_instruction = role_instructions.get(agent_role, "Provide relevant analysis for your expertise area.")
        
        # Section-specific context
        section_contexts = {
            "defense_military_news": "Focus on recent military strategy shifts, procurement priorities, and modernization goals affecting vehicle power systems.",
            "government_solicitations": "Identify active SBIR/STTR, BAA, and RFP opportunities directly supporting bidirectional inverter technology.",
            "technology_advances": "Highlight recent developments in SiC, GaN, thermal solutions, and power electronics innovations.",
            "competitor_updates": "Track competitor activities in vehicle electrification and export power systems.",
            "contract_awards": "Summarize recent DoD awards related to export power and microgrids.",
            "vehicle_power_developments": "List technology adoption and test programs involving bidirectional inverters.",
            "startup_watch": "Identify early-stage startups in electrification, microgrids, or power electronics.",
            "commercial_opportunities": "Identify commercial markets for bidirectional inverter technology."
        }
        
        section_context = section_contexts.get(section_name, "Provide relevant content for this section.")
        
        prompt = f"""
{base_context}

Section Focus: {section_context}

{role_instruction}

Additional Parameters:
{self._format_request_parameters(request_parameters)}

Please provide your contribution focusing on your specific role while ensuring all information is verifiable and includes working source links.
"""
        
        return prompt
    
    def _format_request_parameters(self, parameters: Dict[str, Any]) -> str:
        """Format request parameters for inclusion in prompts"""
        if not parameters:
            return "No additional parameters specified."
        
        formatted = []
        for key, value in parameters.items():
            formatted.append(f"- {key}: {value}")
        
        return "\n".join(formatted)
    
    def _determine_optimal_provider(self, agent_name: str) -> Provider:
        """Determine optimal provider for agent"""
        if agent_name == "TrendTracker":
            return Provider.PERPLEXITY  # Best for research
        elif agent_name in ["Engineer", "TechWiz"]:
            return Provider.GOOGLE  # Good for technical content
        else:
            return Provider.OPENAI  # Default
    
    def _synthesize_contributions(self,
                                 agent_contributions: List[AgentContribution],
                                 section_name: str,
                                 synthesis_method: str = "smart_merge") -> str:
        """
        Synthesize multiple agent contributions into cohesive section content
        
        Args:
            agent_contributions: List of AgentContribution objects
            section_name: Name of the section
            synthesis_method: Method to use: smart_merge, concatenate, primary_only
            
        Returns:
            Synthesized markdown content
        """
        try:
            if not agent_contributions:
                return f"## {section_name.replace('_', ' ').title()}\n\nNo content available."
            
            # Get primary contribution
            primary_contribution = next(
                (c for c in agent_contributions if c.agent_role == "primary"),
                agent_contributions[0] if agent_contributions else None
            )
            
            if synthesis_method == "primary_only":
                # Return only primary content
                content = primary_contribution.content if primary_contribution else ""
                
            elif synthesis_method == "concatenate":
                # Simple concatenation with role labels
                parts = []
                for contrib in agent_contributions:
                    role_label = contrib.agent_role.replace('_', ' ').title()
                    parts.append(f"### {role_label} ({contrib.agent_name})\n\n{contrib.content}")
                content = "\n\n".join(parts)
                
            elif synthesis_method == "smart_merge":
                # Smart merge: primary content with supporting insights integrated
                if not primary_contribution:
                    # Fallback to concatenate if no primary
                    return self._synthesize_contributions(
                        agent_contributions, section_name, "concatenate"
                    )
                
                content = primary_contribution.content
                
                # Add supporting insights from other roles
                supporting_insights = []
                for contrib in agent_contributions:
                    if contrib.agent_role != "primary" and contrib.content:
                        # Only include substantial contributions (>100 chars)
                        if len(contrib.content) > 100:
                            role_label = contrib.agent_role.replace('_', ' ').title()
                            # Check quality score to decide how to present
                            if contrib.quality_score >= 0.8:
                                # High quality - integrate seamlessly
                                supporting_insights.append(
                                    f"\n**{role_label}:** {contrib.content}"
                                )
                            else:
                                # Lower quality - mark clearly
                                supporting_insights.append(
                                    f"\n**{role_label} (Quality: {contrib.quality_score:.2f}):** {contrib.content}"
                                )
                
                if supporting_insights:
                    content = f"{content}\n{''.join(supporting_insights)}"
            
            else:
                # Unknown method, fallback to smart_merge
                logger.warning(f"Unknown synthesis method: {synthesis_method}, using smart_merge")
                return self._synthesize_contributions(
                    agent_contributions, section_name, "smart_merge"
                )
            
            # Add section header if not present
            if not content.startswith("#"):
                section_title = section_name.replace("_", " ").title()
                content = f"## {section_title}\n\n{content}"
            
            return content
            
        except Exception as e:
            logger.error(f"Error synthesizing contributions for {section_name}: {e}")
            return f"## {section_name.replace('_', ' ').title()}\n\nError synthesizing content: {str(e)}"
    
    def _synthesize_section_responses(self, 
                                    section_name: str,
                                    section_responses: Dict[str, Dict[str, Any]],
                                    section_config: Dict[str, Any]) -> str:
        """
        Legacy synthesis method for backwards compatibility
        DEPRECATED: Use _synthesize_contributions instead
        """
        try:
            # Get primary content
            primary_content = ""
            if "primary" in section_responses:
                primary_content = section_responses["primary"]["content"]
            
            # Integrate insights from other roles
            additional_insights = []
            
            for role, response_data in section_responses.items():
                if role != "primary" and response_data["content"]:
                    # Extract key insights from supporting roles
                    content = response_data["content"]
                    if len(content) > 100:  # Only include substantial contributions
                        additional_insights.append(f"\n**{role.replace('_', ' ').title()} Insights:**\n{content}")
            
            # Combine content
            if additional_insights:
                synthesized = f"{primary_content}\n\n{''.join(additional_insights)}"
            else:
                synthesized = primary_content
            
            # Add section header if not present
            if not synthesized.startswith("#"):
                section_title = section_name.replace("_", " ").title()
                synthesized = f"## {section_title}\n\n{synthesized}"
            
            return synthesized
            
        except Exception as e:
            logger.error(f"Error synthesizing section {section_name}: {e}")
            return f"Error synthesizing section content: {str(e)}"
    
    def _compile_report_sections(self, 
                               report_sections: Dict[str, Dict[str, Any]],
                               template_sections: Dict[str, Any]) -> str:
        """
        Compile all sections into complete report using synthesized content
        """
        try:
            report_parts = []
            
            # Add report header
            report_parts.append("# Calnetix Defense & Power Systems Market Intelligence Report")
            report_parts.append(f"**Report Date:** {datetime.now().strftime('%m/%d/%Y')}")
            report_parts.append(f"**Generated by:** CAL Collaborative Intelligence System")
            report_parts.append(f"**Frequency:** Monthly\n")
            
            # Add sections in priority order using synthesized_content
            sorted_sections = sorted(
                report_sections.items(),
                key=lambda x: self.section_priorities.get(x[0], 999)
            )
            
            for section_name, section_data in sorted_sections:
                # Use synthesized_content (new) or fallback to content (legacy)
                section_content = section_data.get("synthesized_content") or section_data.get("content")
                if section_content:
                    report_parts.append(section_content)
                    report_parts.append("")  # Add spacing
            
            # Add generation metadata
            report_parts.append("---")
            report_parts.append("*This report was generated using the CAL Collaborative Intelligence System with fact verification and quality assurance.*")
            
            return "\n".join(report_parts)
            
        except Exception as e:
            logger.error(f"Error compiling report sections: {e}")
            return f"Error compiling report: {str(e)}"
    
    def _generate_report_recommendations(self, 
                                       report_sections: Dict[str, Dict[str, Any]],
                                       overall_quality_assessment) -> List[str]:
        """
        Generate final recommendations based on all sections
        """
        recommendations = []
        
        try:
            # Collect recommendations from quality assessments
            for section_name, section_data in report_sections.items():
                quality_assessment = section_data.get("quality_assessment")
                if quality_assessment and quality_assessment.quality_recommendations:
                    for rec in quality_assessment.quality_recommendations:
                        if rec not in recommendations:
                            recommendations.append(f"[{section_name}] {rec}")
            
            # Add overall recommendations
            if overall_quality_assessment and overall_quality_assessment.quality_recommendations:
                for rec in overall_quality_assessment.quality_recommendations:
                    if rec not in recommendations:
                        recommendations.append(f"[Overall] {rec}")
            
            # Add collaborative-specific recommendations
            recommendations.append("Consider cross-referencing findings across sections for strategic insights")
            recommendations.append("Verify all URLs and sources before final report distribution")
            recommendations.append("Update competitive intelligence based on latest market developments")
            
        except Exception as e:
            logger.error(f"Error generating report recommendations: {e}")
            recommendations.append(f"Error generating recommendations: {str(e)}")
        
        return recommendations
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"market_research_{timestamp}"
    
    async def generate_custom_report(self, request: ReportRequest) -> VerifiedReport:
        """
        Generate custom report based on request parameters
        """
        # This method can be extended for other report types
        if request.report_type == "market_research":
            return await self.generate_market_research(request)
        else:
            raise ValueError(f"Unsupported report type: {request.report_type}")
    
    def get_supported_report_types(self) -> List[str]:
        """Get list of supported report types"""
        return ["market_research"]
    
    def get_section_agents(self, report_type: str) -> Dict[str, Dict[str, str]]:
        """Get agent assignments for report type"""
        if report_type == "market_research":
            return self.report_section_agents
        else:
            return {}
