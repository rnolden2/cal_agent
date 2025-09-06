"""
Template processing system for parsing and managing report templates.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TemplateProcessor:
    """
    Processes report templates and extracts section requirements
    """
    
    def __init__(self):
        # Template section patterns for parsing
        self.section_patterns = {
            "numbered_section": r'^(\d+)\.\s+(.+?)(?=\n\d+\.|$)',
            "header_section": r'^#+\s+(.+?)(?=\n#+|\n\d+\.|$)',
            "table_section": r'\|(.+?)\|',
            "purpose_section": r'Purpose:\s*(.+?)(?=\n[A-Z]|\n\d+\.|$)'
        }
    
    def parse_market_research_template(self) -> Dict[str, Dict[str, Any]]:
        """
        Parse the market research template and extract section configurations
        """
        try:
            # Define sections based on the market_research.txt template
            template_sections = {
                "defense_military_news": {
                    "title": "Defense & Military News Summary",
                    "description": "Provide 2–3 recent news items showing shifts in military strategy, procurement priorities, or modernization goals affecting vehicle power and export power systems. Only include items with a verifiable URL; omit entries without a valid link.",
                    "format": "table",
                    "required_fields": ["headline", "source_date", "impact_relevance"],
                    "verification_required": True,
                    "min_entries": 2,
                    "max_entries": 3
                },
                "government_solicitations": {
                    "title": "Government & DoD Solicitations",
                    "description": "List active and upcoming solicitations (SBIR/STTR, BAA, RFP) directly supporting the Enercycle inverter family. Include title, agency, deadline, and recommended action.",
                    "format": "table",
                    "required_fields": ["solicitation_title", "agency", "deadline", "relevance_action"],
                    "verification_required": True,
                    "focus_areas": ["bidirectional_power_transfer", "lightweight_design", "cost_effective_production", "tms_compatibility", "intelligent_power_distribution"],
                    "min_entries": 1,
                    "max_entries": 5
                },
                "technology_advances": {
                    "title": "Technology & Power Electronics Advances",
                    "description": "Highlight 2–3 recent technical developments (e.g., SiC, GaN, thermal solutions). Include source, valid link, and explain impact on Calnetix technologies.",
                    "format": "table",
                    "required_fields": ["development", "source_date", "potential_impact"],
                    "verification_required": True,
                    "technology_focus": ["SiC", "GaN", "thermal_solutions", "power_electronics"],
                    "min_entries": 2,
                    "max_entries": 3
                },
                "competitor_updates": {
                    "title": "Defense Contractor & Startup Updates",
                    "description": "Track competitor and potential partner activities in vehicle electrification and export power. Only include updates with valid source links.",
                    "format": "table",
                    "required_fields": ["company", "update_with_link", "strategic_takeaway"],
                    "verification_required": True,
                    "key_competitors": ["Aegis Power Systems", "Wittenstein", "GE Aerospace", "RTX Collins Aerospace", "BAE Systems"],
                    "min_entries": 2,
                    "max_entries": 6
                },
                "contract_awards": {
                    "title": "Contract Awards & Funding News",
                    "description": "Summarize recent DoD awards related to export power and microgrids. Include only awards with verifiable announcement links.",
                    "format": "table",
                    "required_fields": ["award_with_link", "recipient", "value", "scope_summary"],
                    "verification_required": True,
                    "focus_areas": ["export_power", "microgrids", "vehicle_power"],
                    "min_entries": 1,
                    "max_entries": 4
                },
                "vehicle_power_developments": {
                    "title": "Export & Onboard Vehicle Power Developments",
                    "description": "List specific technology adoption or test programs involving bidirectional inverters or high-voltage buses. Only include developments with valid source links.",
                    "format": "table",
                    "required_fields": ["development_with_link", "source_date", "enercycle_relevance"],
                    "verification_required": True,
                    "technology_focus": ["bidirectional_inverters", "high_voltage_buses", "vehicle_power"],
                    "min_entries": 1,
                    "max_entries": 3
                },
                "startup_watch": {
                    "title": "Emerging Startup Watch",
                    "description": "Identify early-stage startups with SBIR/venture backing in electrification, microgrids, or power electronics.",
                    "format": "table",
                    "required_fields": ["startup", "focus_area", "funding_status", "opportunity_threat"],
                    "verification_required": False,
                    "focus_areas": ["electrification", "microgrids", "power_electronics"],
                    "min_entries": 2,
                    "max_entries": 5
                },
                "commercial_opportunities": {
                    "title": "Commercial Application Opportunities",
                    "description": "Identify 3–4 commercial markets where bidirectional inverter technology can be applied. Include comprehensive analysis for each opportunity.",
                    "format": "table",
                    "required_fields": ["industry_market", "potential_customers", "current_competitors", "fit_rationale", "fit_risks", "entry_strategy"],
                    "verification_required": False,
                    "market_categories": ["renewable_energy", "marine", "data_centers", "ev_charging"],
                    "min_entries": 3,
                    "max_entries": 4
                },
                "key_takeaways": {
                    "title": "Key Takeaways & Recommendations",
                    "description": "Provide 3–5 bullet points summarizing the most critical strategic actions, risks, or opportunities identified in this report.",
                    "format": "bullet_list",
                    "required_fields": ["strategic_actions", "risks", "opportunities"],
                    "verification_required": False,
                    "min_entries": 3,
                    "max_entries": 5,
                    "dependencies": ["all_previous_sections"]
                }
            }
            
            return template_sections
            
        except Exception as e:
            logger.error(f"Error parsing market research template: {e}")
            return {}
    
    def validate_template_section(self, section_name: str, content: str, section_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate content against template section requirements
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "metrics": {}
        }
        
        try:
            # Check format requirements
            if section_config.get("format") == "table":
                if "|" not in content:
                    validation_result["errors"].append("Table format required but not found")
                    validation_result["valid"] = False
                else:
                    # Count table rows
                    table_rows = content.count("|") // len(section_config.get("required_fields", []))
                    validation_result["metrics"]["table_rows"] = table_rows
                    
                    min_entries = section_config.get("min_entries", 1)
                    max_entries = section_config.get("max_entries", 10)
                    
                    if table_rows < min_entries:
                        validation_result["errors"].append(f"Insufficient entries: {table_rows} found, minimum {min_entries} required")
                        validation_result["valid"] = False
                    elif table_rows > max_entries:
                        validation_result["warnings"].append(f"Many entries: {table_rows} found, maximum {max_entries} recommended")
            
            elif section_config.get("format") == "bullet_list":
                bullet_count = content.count("•") + content.count("-") + content.count("*")
                validation_result["metrics"]["bullet_points"] = bullet_count
                
                min_entries = section_config.get("min_entries", 3)
                max_entries = section_config.get("max_entries", 5)
                
                if bullet_count < min_entries:
                    validation_result["errors"].append(f"Insufficient bullet points: {bullet_count} found, minimum {min_entries} required")
                    validation_result["valid"] = False
                elif bullet_count > max_entries:
                    validation_result["warnings"].append(f"Many bullet points: {bullet_count} found, maximum {max_entries} recommended")
            
            # Check verification requirements
            if section_config.get("verification_required", False):
                url_count = content.count("http")
                validation_result["metrics"]["urls_found"] = url_count
                
                if url_count == 0:
                    validation_result["errors"].append("Verification required but no URLs found")
                    validation_result["valid"] = False
                elif url_count < section_config.get("min_entries", 1):
                    validation_result["warnings"].append("Few verified sources for the number of entries")
            
            # Check required fields presence
            required_fields = section_config.get("required_fields", [])
            for field in required_fields:
                field_indicators = self._get_field_indicators(field)
                if not any(indicator in content.lower() for indicator in field_indicators):
                    validation_result["warnings"].append(f"Required field '{field}' may be missing")
            
            # Check focus areas if specified
            focus_areas = section_config.get("focus_areas", [])
            if focus_areas:
                focus_matches = sum(1 for area in focus_areas if area.lower().replace("_", " ") in content.lower())
                validation_result["metrics"]["focus_area_matches"] = focus_matches
                
                if focus_matches == 0:
                    validation_result["warnings"].append("Content may not align with specified focus areas")
            
            # Check technology focus if specified
            tech_focus = section_config.get("technology_focus", [])
            if tech_focus:
                tech_matches = sum(1 for tech in tech_focus if tech.lower() in content.lower())
                validation_result["metrics"]["technology_matches"] = tech_matches
                
                if tech_matches == 0:
                    validation_result["warnings"].append("Content may not cover specified technologies")
            
            # Check key competitors if specified
            key_competitors = section_config.get("key_competitors", [])
            if key_competitors:
                competitor_matches = sum(1 for comp in key_competitors if comp.lower() in content.lower())
                validation_result["metrics"]["competitor_mentions"] = competitor_matches
                
                if competitor_matches == 0:
                    validation_result["warnings"].append("No key competitors mentioned")
            
        except Exception as e:
            logger.error(f"Error validating template section {section_name}: {e}")
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
        
        return validation_result
    
    def _get_field_indicators(self, field_name: str) -> List[str]:
        """
        Get indicator words/phrases for required fields
        """
        field_indicators = {
            "headline": ["headline", "title", "news"],
            "source_date": ["source", "date", "published"],
            "impact_relevance": ["impact", "relevance", "calnetix", "enercycle"],
            "solicitation_title": ["title", "solicitation", "sbir", "sttr", "baa", "rfp"],
            "agency": ["agency", "army", "navy", "dod", "darpa"],
            "deadline": ["deadline", "due", "closes"],
            "relevance_action": ["relevance", "action", "recommend", "propose"],
            "development": ["development", "advance", "innovation"],
            "potential_impact": ["impact", "benefit", "advantage", "improvement"],
            "company": ["company", "corporation", "inc", "ltd"],
            "update_with_link": ["update", "announcement", "news", "http"],
            "strategic_takeaway": ["strategic", "takeaway", "implication"],
            "award_with_link": ["award", "contract", "http"],
            "recipient": ["recipient", "winner", "contractor"],
            "value": ["value", "$", "million", "billion"],
            "scope_summary": ["scope", "summary", "description"],
            "development_with_link": ["development", "test", "program", "http"],
            "enercycle_relevance": ["enercycle", "inverter", "relevance"],
            "startup": ["startup", "company"],
            "focus_area": ["focus", "area", "domain"],
            "funding_status": ["funding", "series", "sbir", "venture"],
            "opportunity_threat": ["opportunity", "threat", "partner", "competitor"],
            "industry_market": ["industry", "market", "sector"],
            "potential_customers": ["customers", "buyers", "clients"],
            "current_competitors": ["competitors", "competition"],
            "fit_rationale": ["fit", "suitable", "appropriate"],
            "fit_risks": ["risks", "challenges", "concerns"],
            "entry_strategy": ["strategy", "approach", "route"],
            "strategic_actions": ["action", "strategy", "recommend"],
            "risks": ["risk", "threat", "concern"],
            "opportunities": ["opportunity", "potential", "chance"]
        }
        
        return field_indicators.get(field_name, [field_name.replace("_", " ")])
    
    def generate_section_template(self, section_name: str, section_config: Dict[str, Any]) -> str:
        """
        Generate a template structure for a section
        """
        try:
            template_parts = []
            
            # Add section title
            template_parts.append(f"## {section_config.get('title', section_name.replace('_', ' ').title())}")
            template_parts.append("")
            
            # Add description
            if section_config.get("description"):
                template_parts.append(f"**Purpose:** {section_config['description']}")
                template_parts.append("")
            
            # Generate format-specific template
            if section_config.get("format") == "table":
                table_template = self._generate_table_template(section_config)
                template_parts.append(table_template)
            elif section_config.get("format") == "bullet_list":
                bullet_template = self._generate_bullet_template(section_config)
                template_parts.append(bullet_template)
            else:
                template_parts.append("[Content goes here]")
            
            # Add requirements note
            if section_config.get("verification_required"):
                template_parts.append("")
                template_parts.append("*Note: All entries must include verifiable sources with working URLs.*")
            
            return "\n".join(template_parts)
            
        except Exception as e:
            logger.error(f"Error generating section template for {section_name}: {e}")
            return f"## {section_name.replace('_', ' ').title()}\n\n[Template generation error]"
    
    def _generate_table_template(self, section_config: Dict[str, Any]) -> str:
        """
        Generate table template based on required fields
        """
        required_fields = section_config.get("required_fields", ["Field1", "Field2"])
        
        # Create header row
        headers = [field.replace("_", " ").title() for field in required_fields]
        header_row = "| " + " | ".join(headers) + " |"
        
        # Create separator row
        separator_row = "|" + "|".join(["-" * (len(header) + 2) for header in headers]) + "|"
        
        # Create example rows
        example_rows = []
        min_entries = section_config.get("min_entries", 1)
        
        for i in range(min_entries):
            example_values = []
            for field in required_fields:
                if "link" in field.lower():
                    example_values.append(f"[Example {field.replace('_', ' ')}](https://example.com)")
                elif "date" in field.lower():
                    example_values.append("MM/DD/YYYY")
                elif "value" in field.lower() or "funding" in field.lower():
                    example_values.append("$XX M")
                else:
                    example_values.append(f"[Example {field.replace('_', ' ')}]")
            
            example_row = "| " + " | ".join(example_values) + " |"
            example_rows.append(example_row)
        
        return "\n".join([header_row, separator_row] + example_rows)
    
    def _generate_bullet_template(self, section_config: Dict[str, Any]) -> str:
        """
        Generate bullet list template
        """
        min_entries = section_config.get("min_entries", 3)
        required_fields = section_config.get("required_fields", ["item"])
        
        bullet_items = []
        for i in range(min_entries):
            if "strategic_actions" in required_fields:
                bullet_items.append(f"• **Action {i+1}:** [Describe strategic action or recommendation]")
            elif "risks" in required_fields:
                bullet_items.append(f"• **Risk {i+1}:** [Identify potential risk or challenge]")
            elif "opportunities" in required_fields:
                bullet_items.append(f"• **Opportunity {i+1}:** [Describe market opportunity]")
            else:
                bullet_items.append(f"• [Item {i+1}]: [Description]")
        
        return "\n".join(bullet_items)
    
    def extract_template_metadata(self, template_content: str) -> Dict[str, Any]:
        """
        Extract metadata from template content
        """
        metadata = {
            "sections_found": [],
            "total_sections": 0,
            "verification_sections": 0,
            "table_sections": 0,
            "estimated_complexity": "medium",
            "agent_requirements": {},
            "dependency_map": {},
            "quality_requirements": {}
        }
        
        try:
            # Find numbered sections
            numbered_sections = re.findall(r'^(\d+)\.\s+(.+?)$', template_content, re.MULTILINE)
            metadata["sections_found"] = [section[1] for section in numbered_sections]
            metadata["total_sections"] = len(numbered_sections)
            
            # Count verification requirements
            verification_count = template_content.lower().count("verifiable") + template_content.lower().count("valid link")
            metadata["verification_sections"] = verification_count
            
            # Count table sections
            table_count = template_content.count("|")
            metadata["table_sections"] = table_count // 10  # Rough estimate
            
            # Extract agent requirements from content
            metadata["agent_requirements"] = self._extract_agent_requirements(template_content)
            
            # Extract dependencies
            metadata["dependency_map"] = self._extract_section_dependencies(template_content)
            
            # Extract quality requirements
            metadata["quality_requirements"] = self._extract_quality_requirements(template_content)
            
            # Estimate complexity
            complexity_score = (
                metadata["total_sections"] * 0.4 +
                metadata["verification_sections"] * 0.3 +
                metadata["table_sections"] * 0.3
            )
            
            if complexity_score < 5:
                metadata["estimated_complexity"] = "low"
            elif complexity_score < 10:
                metadata["estimated_complexity"] = "medium"
            else:
                metadata["estimated_complexity"] = "high"
            
        except Exception as e:
            logger.error(f"Error extracting template metadata: {e}")
        
        return metadata
    
    def get_supported_templates(self) -> List[str]:
        """
        Get list of supported template types
        """
        return ["market_research"]
    
    def parse_custom_template(self, template_content: str, template_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Parse custom template content (extensible for future template types)
        """
        if template_type == "market_research":
            return self.parse_market_research_template()
        else:
            # Generic parsing for unknown template types
            return self._parse_generic_template(template_content)
    
    def _parse_generic_template(self, template_content: str) -> Dict[str, Dict[str, Any]]:
        """
        Generic template parsing for unknown formats
        """
        sections = {}
        
        try:
            # Find numbered sections
            numbered_sections = re.findall(r'^(\d+)\.\s+(.+?)(?=\n\d+\.|$)', template_content, re.MULTILINE | re.DOTALL)
            
            for i, (number, content) in enumerate(numbered_sections):
                section_name = f"section_{number}"
                
                # Extract title from first line
                lines = content.strip().split('\n')
                title = lines[0] if lines else f"Section {number}"
                
                sections[section_name] = {
                    "title": title,
                    "description": content.strip(),
                    "format": "table" if "|" in content else "text",
                    "verification_required": "verifiable" in content.lower() or "link" in content.lower(),
                    "priority": i + 1,
                    "required_fields": self._extract_required_fields(content),
                    "focus_areas": self._extract_focus_areas(content),
                    "min_entries": self._extract_min_entries(content),
                    "max_entries": self._extract_max_entries(content)
                }
        
        except Exception as e:
            logger.error(f"Error parsing generic template: {e}")
        
        return sections
    
    def _extract_agent_requirements(self, template_content: str) -> Dict[str, List[str]]:
        """
        Extract agent requirements from template content
        """
        agent_requirements = {}
        
        # Keywords that suggest specific agent needs
        agent_keywords = {
            "TrendTracker": ["market", "trend", "research", "news", "solicitation", "award"],
            "Engineer": ["technical", "technology", "specification", "development", "power", "electronics"],
            "RivalWatcher": ["competitor", "startup", "company", "rival", "partnership"],
            "Sales": ["commercial", "opportunity", "business", "customer", "market", "revenue"],
            "Editor": ["format", "structure", "consistency", "style"],
            "DocumentMaster": ["template", "organization", "layout", "presentation"]
        }
        
        content_lower = template_content.lower()
        
        for agent, keywords in agent_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
            if keyword_count > 0:
                agent_requirements[agent] = keywords[:keyword_count]
        
        return agent_requirements
    
    def _extract_section_dependencies(self, template_content: str) -> Dict[str, List[str]]:
        """
        Extract section dependencies from template content
        """
        dependencies = {}
        
        # Look for dependency indicators
        dependency_patterns = [
            r'based on (.+?) section',
            r'building on (.+?) analysis',
            r'following (.+?) findings',
            r'incorporating (.+?) insights'
        ]
        
        sections = re.findall(r'^(\d+)\.\s+(.+?)$', template_content, re.MULTILINE)
        
        for number, section_title in sections:
            section_deps = []
            
            # Check for dependency patterns in section content
            section_content = self._extract_section_content(template_content, number)
            
            for pattern in dependency_patterns:
                matches = re.findall(pattern, section_content.lower())
                section_deps.extend(matches)
            
            if section_deps:
                dependencies[f"section_{number}"] = section_deps
        
        return dependencies
    
    def _extract_quality_requirements(self, template_content: str) -> Dict[str, float]:
        """
        Extract quality requirements from template content
        """
        quality_requirements = {}
        
        # Default quality thresholds based on content analysis
        if "verifiable" in template_content.lower():
            quality_requirements["verification_threshold"] = 0.9
        else:
            quality_requirements["verification_threshold"] = 0.7
        
        if "critical" in template_content.lower() or "essential" in template_content.lower():
            quality_requirements["content_quality_threshold"] = 0.85
        else:
            quality_requirements["content_quality_threshold"] = 0.75
        
        # Count of quality indicators
        quality_indicators = template_content.lower().count("accurate") + \
                           template_content.lower().count("verified") + \
                           template_content.lower().count("reliable")
        
        quality_requirements["quality_emphasis_score"] = min(quality_indicators / 10.0, 1.0)
        
        return quality_requirements
    
    def _extract_section_content(self, template_content: str, section_number: str) -> str:
        """
        Extract content for a specific section number
        """
        pattern = rf'^{section_number}\.\s+(.+?)(?=\n\d+\.|$)'
        match = re.search(pattern, template_content, re.MULTILINE | re.DOTALL)
        return match.group(1) if match else ""
    
    def _extract_required_fields(self, content: str) -> List[str]:
        """
        Extract required fields from section content
        """
        # Look for field indicators in table headers or descriptions
        field_patterns = [
            r'\|([^|]+)\|',  # Table headers
            r'include (.+?) and (.+?)(?:\.|,)',  # "include X and Y"
            r'provide (.+?)(?:\.|,)',  # "provide X"
            r'list (.+?)(?:\.|,)'  # "list X"
        ]
        
        fields = []
        for pattern in field_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    fields.extend([m.strip() for m in match])
                else:
                    fields.append(match.strip())
        
        # Clean and deduplicate
        cleaned_fields = []
        for field in fields:
            field = field.lower().replace(" ", "_")
            if field and field not in cleaned_fields and len(field) < 50:
                cleaned_fields.append(field)
        
        return cleaned_fields[:10]  # Limit to reasonable number
    
    def _extract_focus_areas(self, content: str) -> List[str]:
        """
        Extract focus areas from section content
        """
        focus_keywords = [
            "defense", "military", "power", "electronics", "inverter", "microgrid",
            "vehicle", "export", "bidirectional", "sic", "gan", "thermal",
            "startup", "competitor", "commercial", "market", "technology"
        ]
        
        content_lower = content.lower()
        found_areas = [keyword for keyword in focus_keywords if keyword in content_lower]
        
        return found_areas
    
    def _extract_min_entries(self, content: str) -> int:
        """
        Extract minimum entries requirement from content
        """
        min_patterns = [
            r'(\d+)[-–]?\d*\s+(?:items?|entries?|examples?)',
            r'minimum\s+(\d+)',
            r'at least\s+(\d+)',
            r'provide\s+(\d+)'
        ]
        
        for pattern in min_patterns:
            match = re.search(pattern, content.lower())
            if match:
                return int(match.group(1))
        
        return 1  # Default minimum
    
    def _extract_max_entries(self, content: str) -> int:
        """
        Extract maximum entries requirement from content
        """
        max_patterns = [
            r'\d+[-–](\d+)\s+(?:items?|entries?|examples?)',
            r'maximum\s+(\d+)',
            r'up to\s+(\d+)',
            r'no more than\s+(\d+)'
        ]
        
        for pattern in max_patterns:
            match = re.search(pattern, content.lower())
            if match:
                return int(match.group(1))
        
        return 10  # Default maximum
    
    def process_template_with_context(self, 
                                    template_name: str, 
                                    context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process template with additional context data for enhanced generation
        """
        try:
            # Get base template configuration
            if template_name == "market_research":
                template_config = self.parse_market_research_template()
            else:
                template_config = {}
            
            # Enhance with context data
            enhanced_config = {}
            
            for section_name, section_config in template_config.items():
                enhanced_section = section_config.copy()
                
                # Add context-specific enhancements
                if "user_preferences" in context_data:
                    enhanced_section["user_preferences"] = context_data["user_preferences"]
                
                if "historical_feedback" in context_data:
                    enhanced_section["feedback_context"] = context_data["historical_feedback"]
                
                if "priority_adjustments" in context_data:
                    priority_adj = context_data["priority_adjustments"].get(section_name, 0)
                    enhanced_section["adjusted_priority"] = enhanced_section.get("priority", 5) + priority_adj
                
                # Add dynamic requirements based on context
                if "focus_areas" in context_data:
                    enhanced_section["dynamic_focus"] = context_data["focus_areas"]
                
                enhanced_config[section_name] = enhanced_section
            
            return enhanced_config
            
        except Exception as e:
            logger.error(f"Error processing template with context: {e}")
            return template_config if 'template_config' in locals() else {}
    
    def validate_template_completeness(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that template configuration is complete and consistent
        """
        validation_result = {
            "complete": True,
            "missing_elements": [],
            "inconsistencies": [],
            "recommendations": []
        }
        
        try:
            required_elements = [
                "title", "description", "format", "required_fields"
            ]
            
            for section_name, section_config in template_config.items():
                # Check required elements
                for element in required_elements:
                    if element not in section_config:
                        validation_result["missing_elements"].append(f"{section_name}: {element}")
                        validation_result["complete"] = False
                
                # Check format consistency
                if section_config.get("format") == "table":
                    if not section_config.get("required_fields"):
                        validation_result["inconsistencies"].append(f"{section_name}: Table format but no required fields")
                
                # Check verification requirements
                if section_config.get("verification_required") and not section_config.get("min_entries"):
                    validation_result["recommendations"].append(f"{section_name}: Consider setting minimum entries for verification")
            
            # Check overall consistency
            total_sections = len(template_config)
            if total_sections > 10:
                validation_result["recommendations"].append("Consider reducing number of sections for better focus")
            elif total_sections < 3:
                validation_result["recommendations"].append("Consider adding more sections for comprehensive coverage")
            
        except Exception as e:
            logger.error(f"Error validating template completeness: {e}")
            validation_result["complete"] = False
            validation_result["missing_elements"].append(f"Validation error: {str(e)}")
        
        return validation_result
