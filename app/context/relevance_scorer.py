"""
Advanced relevance scoring system for feedback integration.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..orchestrator.agent_capabilities import get_feedback_categories_for_agent, FEEDBACK_CATEGORIES

@dataclass
class FeedbackEntry:
    """Enhanced feedback entry with metadata"""
    content: str
    category: str
    timestamp: datetime
    source: str  # presentation, meeting, document_review, etc.
    context: str  # Army presentation, customer meeting, etc.
    relevance_score: float = 0.0
    impact_score: float = 0.0
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []

class RelevanceScorer:
    """
    Advanced feedback relevance scoring system
    """
    
    def __init__(self):
        # Keyword patterns extracted from feedback.txt analysis
        self.category_keywords = {
            "presentation_skills": [
                "tone", "cadence", "presentation mode", "full screen", "monotone",
                "verbose", "connection to needs", "over-explaining", "clarity",
                "fumbling", "explaining", "prepared", "testing", "ambiguous tasks"
            ],
            "technical_accuracy": [
                "company claims", "technology", "motor/generator", "AMBs", "high speed",
                "DOE", "Navy", "Army", "export power", "inverter", "requirements",
                "implementation", "topology", "efficiency", "parallel operation",
                "bi-directional", "MOSA compliant", "switching modules", "thermal analysis"
            ],
            "business_focus": [
                "customer needs", "business opportunity", "revenue", "quantities",
                "market share", "government funding", "tactical vehicles", "competitors",
                "salesforce", "relationships", "business side", "ROMs", "price",
                "market research", "industrial side", "HESC", "DC1000 development"
            ],
            "communication_style": [
                "professional", "audience", "message", "persuasive", "concise",
                "over communicate", "priority", "customer responses", "visuals",
                "PowerPoint", "supplement", "interaction", "meeting"
            ],
            "research_depth": [
                "market research", "data", "analysis", "comprehensive", "sources",
                "elaborate", "information", "details", "knowing the customer",
                "company history", "competitors", "system perspective"
            ]
        }
        
        # Context importance weights
        self.context_weights = {
            "army_presentation": 1.0,
            "customer_meeting": 0.9,
            "requirements_review": 0.8,
            "document_review": 0.7,
            "internal_feedback": 0.6,
            "general_feedback": 0.5
        }
        
        # Task type relevance mapping
        self.task_relevance = {
            "market_research": {
                "business_focus": 1.0,
                "research_depth": 0.9,
                "technical_accuracy": 0.7,
                "presentation_skills": 0.6,
                "communication_style": 0.5
            },
            "competitor_analysis": {
                "business_focus": 1.0,
                "research_depth": 0.9,
                "technical_accuracy": 0.6,
                "presentation_skills": 0.5,
                "communication_style": 0.5
            },
            "technical_analysis": {
                "technical_accuracy": 1.0,
                "research_depth": 0.8,
                "business_focus": 0.7,
                "presentation_skills": 0.6,
                "communication_style": 0.5
            },
            "customer_communication": {
                "presentation_skills": 1.0,
                "communication_style": 0.9,
                "business_focus": 0.8,
                "technical_accuracy": 0.6,
                "research_depth": 0.5
            },
            "business_strategy": {
                "business_focus": 1.0,
                "presentation_skills": 0.8,
                "communication_style": 0.7,
                "research_depth": 0.7,
                "technical_accuracy": 0.6
            }
        }
    
    def parse_feedback_from_text(self, feedback_text: str) -> List[FeedbackEntry]:
        """
        Parse the feedback.txt content into structured feedback entries
        """
        entries = []
        
        # Split by clear section breaks and dates
        sections = re.split(r'\n(?=\d{1,2}/\d{1,2}/\d{2,4}|\w+:|\d+\.)', feedback_text)
        
        for section in sections:
            if not section.strip():
                continue
                
            # Extract context and categorize
            context = self._extract_context(section)
            category = self._categorize_feedback_content(section)
            
            if category:
                # Extract individual feedback points
                feedback_points = self._extract_feedback_points(section)
                
                for point in feedback_points:
                    if len(point.strip()) > 10:  # Filter out very short entries
                        entry = FeedbackEntry(
                            content=point.strip(),
                            category=category,
                            timestamp=self._extract_timestamp(section),
                            source=self._extract_source(section),
                            context=context,
                            keywords=self._extract_keywords(point, category)
                        )
                        entries.append(entry)
        
        return entries
    
    def score_feedback_relevance(self, 
                                feedback_entries: List[FeedbackEntry], 
                                task_type: str, 
                                agent_names: List[str],
                                current_content: str = "") -> List[FeedbackEntry]:
        """
        Score feedback relevance to current task and agents
        """
        for entry in feedback_entries:
            score = 0.0
            
            # 1. Category relevance to task type (40% weight)
            task_relevance = self.task_relevance.get(task_type, {})
            category_weight = task_relevance.get(entry.category, 0.3)
            score += category_weight * 0.4
            
            # 2. Agent relevance (25% weight)
            agent_score = 0.0
            for agent_name in agent_names:
                agent_categories = get_feedback_categories_for_agent(agent_name)
                if entry.category in agent_categories:
                    agent_score += 0.5
            score += min(agent_score, 1.0) * 0.25
            
            # 3. Recency score (15% weight)
            days_old = (datetime.now() - entry.timestamp).days
            recency_score = max(0, 1.0 - (days_old / 90))  # Decay over 90 days
            score += recency_score * 0.15
            
            # 4. Context importance (10% weight)
            context_key = self._normalize_context(entry.context)
            context_weight = self.context_weights.get(context_key, 0.5)
            score += context_weight * 0.1
            
            # 5. Content relevance to current request (10% weight)
            if current_content:
                content_relevance = self._calculate_content_similarity(
                    entry.content, current_content
                )
                score += content_relevance * 0.1
            
            entry.relevance_score = min(1.0, score)
        
        # Sort by relevance score (highest first)
        return sorted(feedback_entries, key=lambda x: x.relevance_score, reverse=True)
    
    def _extract_context(self, section: str) -> str:
        """Extract context from feedback section"""
        section_lower = section.lower()
        
        if "army" in section_lower:
            return "army_presentation"
        elif "customer" in section_lower:
            return "customer_meeting"
        elif "requirements" in section_lower:
            return "requirements_review"
        elif "presentation slides" in section_lower or "ppt" in section_lower:
            return "document_review"
        elif "meeting" in section_lower:
            return "internal_feedback"
        else:
            return "general_feedback"
    
    def _categorize_feedback_content(self, content: str) -> Optional[str]:
        """Categorize feedback content based on keywords"""
        content_lower = content.lower()
        
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 1
            category_scores[category] = score
        
        # Return category with highest score, or None if no matches
        if category_scores and max(category_scores.values()) > 0:
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def _extract_feedback_points(self, section: str) -> List[str]:
        """Extract individual feedback points from a section"""
        # Split by numbered lists, bullet points, or line breaks
        points = []
        
        # Handle numbered lists
        numbered_matches = re.findall(r'\d+\.\s*([^0-9]+?)(?=\d+\.|$)', section, re.DOTALL)
        if numbered_matches:
            points.extend([match.strip() for match in numbered_matches])
        
        # Handle lettered sub-points
        lettered_matches = re.findall(r'[a-z]\.\s*([^a-z]+?)(?=[a-z]\.|$)', section, re.DOTALL)
        if lettered_matches:
            points.extend([match.strip() for match in lettered_matches])
        
        # Handle bullet points or general statements
        if not points:
            lines = section.split('\n')
            for line in lines:
                line = line.strip()
                if len(line) > 20 and not re.match(r'^\d{1,2}/\d{1,2}/\d{2,4}', line):
                    points.append(line)
        
        return points
    
    def _extract_timestamp(self, section: str) -> datetime:
        """Extract timestamp from section, default to recent if not found"""
        # Look for date patterns
        date_match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', section)
        if date_match:
            month, day, year = date_match.groups()
            year = int(year)
            if year < 100:  # Handle 2-digit years
                year += 2000
            try:
                return datetime(year, int(month), int(day))
            except ValueError:
                pass
        
        # Default to 30 days ago if no date found
        return datetime.now() - timedelta(days=30)
    
    def _extract_source(self, section: str) -> str:
        """Extract source type from section"""
        section_lower = section.lower()
        
        if "presentation" in section_lower:
            return "presentation"
        elif "meeting" in section_lower:
            return "meeting"
        elif "review" in section_lower:
            return "document_review"
        elif "feedback" in section_lower:
            return "feedback_session"
        else:
            return "general"
    
    def _extract_keywords(self, content: str, category: str) -> List[str]:
        """Extract relevant keywords from content"""
        keywords = []
        content_lower = content.lower()
        
        # Get category-specific keywords that appear in content
        category_keywords = self.category_keywords.get(category, [])
        for keyword in category_keywords:
            if keyword.lower() in content_lower:
                keywords.append(keyword)
        
        return keywords
    
    def _normalize_context(self, context: str) -> str:
        """Normalize context string for lookup"""
        return context.lower().replace(" ", "_")
    
    def _calculate_content_similarity(self, feedback_content: str, current_content: str) -> float:
        """Calculate similarity between feedback and current content"""
        feedback_words = set(feedback_content.lower().split())
        current_words = set(current_content.lower().split())
        
        if not feedback_words or not current_words:
            return 0.0
        
        intersection = feedback_words.intersection(current_words)
        union = feedback_words.union(current_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def get_top_relevant_feedback(self, 
                                 feedback_entries: List[FeedbackEntry],
                                 task_type: str,
                                 agent_names: List[str],
                                 current_content: str = "",
                                 limit: int = 10) -> List[FeedbackEntry]:
        """
        Get top relevant feedback entries for current context
        """
        scored_feedback = self.score_feedback_relevance(
            feedback_entries, task_type, agent_names, current_content
        )
        
        # Filter out very low relevance scores
        relevant_feedback = [f for f in scored_feedback if f.relevance_score > 0.3]
        
        return relevant_feedback[:limit]
