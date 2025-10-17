"""
Manages the integration of feedback into agent prompts.
"""
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime, timedelta

try:
    from google.cloud import storage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    storage = None

from ..storage.firestore_db import get_agent_responses, get_feedback
from ..orchestrator.agent_capabilities import get_feedback_categories_for_agent, FEEDBACK_CATEGORIES
from .relevance_scorer import RelevanceScorer, FeedbackEntry
from ..utils.feedback_processor import FeedbackFileProcessor

logger = logging.getLogger(__name__)

class FeedbackContextManager:
    """
    Enhanced feedback integration into agent prompts with advanced relevance scoring
    """
    
    def __init__(self):
        self.feedback_cache = {}
        self.cache_expiry = timedelta(hours=1)
        self.relevance_scorer = RelevanceScorer()
        self.parsed_feedback_entries = None
        self._feedback_loaded = False
    
    async def get_relevant_feedback(self, 
                                  task_type: str, 
                                  agent_names: List[str],
                                  user_id: str,
                                  current_content: str = "",
                                  limit: int = 10) -> List[FeedbackEntry]:
        """
        Retrieve feedback relevant to current task and agents using advanced scoring
        """
        try:
            # Load feedback from both static files and Firestore
            all_feedback_entries = []
            
            # 1. Load from processed files and static feedback if not already loaded
            if not self._feedback_loaded:
                await self._load_feedback_data()
                self._feedback_loaded = True
            
            if self.parsed_feedback_entries:
                all_feedback_entries.extend(self.parsed_feedback_entries)
            
            # 2. Load from Firestore database
            try:
                firestore_feedback = await get_feedback(user_id=user_id, limit=100)
                for fb_doc in firestore_feedback:
                    # Convert Firestore document to FeedbackEntry
                    entry = FeedbackEntry(
                        content=fb_doc.get("feedback_text", ""),
                        category=fb_doc.get("category", "general"),
                        timestamp=fb_doc.get("timestamp", datetime.now()),
                        source=fb_doc.get("source", "boss_feedback"),
                        context=fb_doc.get("context", ""),
                        keywords=[]
                    )
                    all_feedback_entries.append(entry)
                
                logger.info(f"Loaded {len(firestore_feedback)} feedback entries from Firestore")
            except Exception as e:
                logger.warning(f"Could not load feedback from Firestore: {e}")
            
            if not all_feedback_entries:
                logger.warning("No feedback entries available from any source")
                return []
            
            # Get top relevant feedback using the advanced scorer
            relevant_feedback = self.relevance_scorer.get_top_relevant_feedback(
                feedback_entries=all_feedback_entries,
                task_type=task_type,
                agent_names=agent_names,
                current_content=current_content,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(relevant_feedback)} relevant feedback entries for task_type: {task_type}")
            
            return relevant_feedback
            
        except Exception as e:
            logger.error(f"Error retrieving feedback: {e}")
            return []
    
    def inject_feedback_context(self, 
                              prompt: str, 
                              feedback: List[FeedbackEntry],
                              agent_name: str) -> str:
        """
        Inject feedback as context into agent prompts with enhanced formatting
        """
        if not feedback:
            return prompt
        
        # Categorize feedback by type
        categorized_feedback = self._categorize_feedback(feedback)
        
        context_parts = ["=" * 80]
        context_parts.append("CRITICAL CONTEXT FROM PREVIOUS FEEDBACK")
        context_parts.append("=" * 80)
        context_parts.append("")
        
        # Add presentation & communication feedback
        if categorized_feedback.get("presentation_skills"):
            context_parts.append("🎯 PRESENTATION & COMMUNICATION IMPROVEMENTS:")
            for entry in categorized_feedback["presentation_skills"]:
                relevance = f"(Relevance: {entry.relevance_score:.2f})"
                context_parts.append(f"  • {entry.content} {relevance}")
            context_parts.append("")
        
        # Add technical accuracy feedback
        if categorized_feedback.get("technical_accuracy"):
            context_parts.append("🔧 TECHNICAL ACCURACY REQUIREMENTS:")
            for entry in categorized_feedback["technical_accuracy"]:
                relevance = f"(Relevance: {entry.relevance_score:.2f})"
                context_parts.append(f"  • {entry.content} {relevance}")
            context_parts.append("")
        
        # Add business focus feedback
        if categorized_feedback.get("business_focus"):
            context_parts.append("💼 BUSINESS FOCUS GUIDELINES:")
            for entry in categorized_feedback["business_focus"]:
                relevance = f"(Relevance: {entry.relevance_score:.2f})"
                context_parts.append(f"  • {entry.content} {relevance}")
            context_parts.append("")
        
        # Add communication style feedback
        if categorized_feedback.get("communication_style"):
            context_parts.append("💬 COMMUNICATION STYLE GUIDELINES:")
            for entry in categorized_feedback["communication_style"]:
                relevance = f"(Relevance: {entry.relevance_score:.2f})"
                context_parts.append(f"  • {entry.content} {relevance}")
            context_parts.append("")
        
        # Add research depth feedback
        if categorized_feedback.get("research_depth"):
            context_parts.append("📊 RESEARCH DEPTH REQUIREMENTS:")
            for entry in categorized_feedback["research_depth"]:
                relevance = f"(Relevance: {entry.relevance_score:.2f})"
                context_parts.append(f"  • {entry.content} {relevance}")
            context_parts.append("")
        
        # Add agent-specific feedback for other categories
        agent_categories = get_feedback_categories_for_agent(agent_name)
        for category in agent_categories:
            if category in categorized_feedback and category not in [
                "presentation_skills", "technical_accuracy", "business_focus", 
                "communication_style", "research_depth"
            ]:
                context_parts.append(f"📋 {category.replace('_', ' ').upper()} GUIDELINES:")
                for entry in categorized_feedback[category]:
                    relevance = f"(Relevance: {entry.relevance_score:.2f})"
                    context_parts.append(f"  • {entry.content} {relevance}")
                context_parts.append("")
        
        context_parts.append("=" * 80)
        context_parts.append("ORIGINAL REQUEST:")
        context_parts.append("=" * 80)
        context_parts.append(prompt)
        context_parts.append("")
        context_parts.append("IMPORTANT: Please incorporate the above feedback context into your response.")
        
        return "\n".join(context_parts)
    
    async def _load_feedback_data(self):
        """
        Load and parse feedback data from multiple sources including processed cloud storage files
        """
        try:
            all_feedback_entries = []
            
            # 1. Load from processed feedback files (NEW FEATURE)
            try:
                processor = FeedbackFileProcessor()
                processed_entries = await processor.get_processed_feedback_entries()
                all_feedback_entries.extend(processed_entries)
                logger.info(f"Loaded {len(processed_entries)} feedback entries from processed cloud storage files")
            except Exception as e:
                logger.warning(f"Could not load processed feedback files: {e}")
            
            # 2. Load from static feedback.txt file (LEGACY SUPPORT)
            if STORAGE_AVAILABLE:
                try:
                    # Configuration for GCS bucket and blob
                    bucket_name = "api-project-371618.appspot.com"
                    blob_path = "resources/feedback.txt"
                    
                    # Initialize the Storage client (uses ADC automatically)
                    client = storage.Client()
                    bucket = client.bucket(bucket_name)
                    blob = bucket.blob(blob_path)
                    
                    # Download the blob content as text
                    feedback_text = blob.download_as_text(encoding='utf-8')
                    
                    static_entries = self.relevance_scorer.parse_feedback_from_text(feedback_text)
                    all_feedback_entries.extend(static_entries)
                    logger.info(f"Loaded {len(static_entries)} feedback entries from static feedback.txt")
                    
                except Exception as e:
                    logger.error(f"Failed to fetch static feedback from Google Cloud Storage: {e}")
            else:
                logger.warning("Google Cloud Storage client not available")
            
            # 3. Fallback to local file if cloud storage fails
            if not all_feedback_entries:
                feedback_file_path = os.path.join(
                    os.path.dirname(__file__), 
                    "..", "resources", "templates", "feedback.txt"
                )
                
                if os.path.exists(feedback_file_path):
                    logger.info("Falling back to local feedback file")
                    with open(feedback_file_path, 'r', encoding='utf-8') as f:
                        feedback_text = f.read()
                    
                    fallback_entries = self.relevance_scorer.parse_feedback_from_text(feedback_text)
                    all_feedback_entries.extend(fallback_entries)
                    logger.info(f"Loaded {len(fallback_entries)} feedback entries from local fallback")
            
            # Store all entries
            self.parsed_feedback_entries = all_feedback_entries
            
            if not self.parsed_feedback_entries:
                logger.warning("No feedback entries available from any source")
            else:
                logger.info(f"Total feedback entries loaded: {len(self.parsed_feedback_entries)} from all sources")
                
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
            self.parsed_feedback_entries = []
    
    def get_feedback_impact_metrics(self, agent_name: str, task_type: str) -> Dict[str, Any]:
        """
        Get feedback impact metrics for reporting and improvement tracking
        """
        if not self.parsed_feedback_entries:
            return {}
        
        agent_categories = get_feedback_categories_for_agent(agent_name)
        relevant_feedback = [f for f in self.parsed_feedback_entries if f.category in agent_categories]
        
        metrics = {
            "total_feedback_entries": len(relevant_feedback),
            "categories_covered": list(set(f.category for f in relevant_feedback)),
            "average_relevance_score": sum(f.relevance_score for f in relevant_feedback) / len(relevant_feedback) if relevant_feedback else 0,
            "recent_feedback_count": len([f for f in relevant_feedback if (datetime.now() - f.timestamp).days <= 30]),
            "high_impact_feedback": len([f for f in relevant_feedback if f.relevance_score > 0.7])
        }
        
        return metrics
    
    def _categorize_feedback(self, feedback: List[FeedbackEntry]) -> Dict[str, List[FeedbackEntry]]:
        """
        Categorize feedback entries by type
        """
        categorized = {}
        for entry in feedback:
            if entry.category not in categorized:
                categorized[entry.category] = []
            categorized[entry.category].append(entry)
        
        return categorized

# Legacy class name for backward compatibility
class FeedbackManager(FeedbackContextManager):
    """Backward compatibility alias"""
    pass
