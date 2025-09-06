"""
Feedback impact tracking system for measuring improvement over time.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from ..storage.firestore_db import store_agent_response
from .relevance_scorer import FeedbackEntry

logger = logging.getLogger(__name__)

@dataclass
class FeedbackImpactMetric:
    """Represents a feedback impact measurement"""
    workflow_id: str
    user_id: str
    task_type: str
    agents_involved: List[str]
    feedback_categories_applied: List[str]
    feedback_entries_count: int
    average_relevance_score: float
    response_quality_score: float
    timestamp: datetime
    improvement_indicators: Dict[str, Any]

class FeedbackImpactTracker:
    """
    Tracks the impact of feedback integration on agent performance
    """
    
    def __init__(self):
        self.impact_metrics = []
        self.baseline_metrics = {}
        
        # Define improvement indicators based on feedback categories
        self.improvement_indicators = {
            "presentation_skills": [
                "clarity_score", "engagement_score", "structure_score",
                "audience_awareness_score", "conciseness_score"
            ],
            "technical_accuracy": [
                "fact_accuracy_score", "source_reliability_score", 
                "technical_depth_score", "implementation_clarity_score"
            ],
            "business_focus": [
                "customer_needs_alignment", "business_opportunity_identification",
                "market_relevance_score", "revenue_focus_score"
            ],
            "communication_style": [
                "professional_tone_score", "message_clarity_score",
                "persuasiveness_score", "audience_adaptation_score"
            ],
            "research_depth": [
                "source_quality_score", "data_comprehensiveness",
                "analysis_depth_score", "trend_identification_score"
            ]
        }
    
    def track_feedback_application(self, 
                                 workflow_id: str,
                                 user_id: str,
                                 task_type: str,
                                 agents_involved: List[str],
                                 feedback_entries: List[FeedbackEntry],
                                 response_content: str) -> FeedbackImpactMetric:
        """
        Track the application of feedback in a workflow
        """
        try:
            # Calculate metrics
            feedback_categories = list(set(f.category for f in feedback_entries))
            avg_relevance = sum(f.relevance_score for f in feedback_entries) / len(feedback_entries) if feedback_entries else 0.0
            
            # Analyze response quality based on feedback categories
            quality_score = self._calculate_response_quality_score(
                response_content, feedback_categories, feedback_entries
            )
            
            # Calculate improvement indicators
            improvement_indicators = self._calculate_improvement_indicators(
                response_content, feedback_categories, feedback_entries
            )
            
            # Create impact metric
            impact_metric = FeedbackImpactMetric(
                workflow_id=workflow_id,
                user_id=user_id,
                task_type=task_type,
                agents_involved=agents_involved,
                feedback_categories_applied=feedback_categories,
                feedback_entries_count=len(feedback_entries),
                average_relevance_score=avg_relevance,
                response_quality_score=quality_score,
                timestamp=datetime.now(),
                improvement_indicators=improvement_indicators
            )
            
            # Store the metric
            self.impact_metrics.append(impact_metric)
            
            # Store in Firestore for persistence
            self._store_impact_metric(impact_metric)
            
            logger.info(f"Tracked feedback impact for workflow {workflow_id}: Quality Score {quality_score:.2f}")
            
            return impact_metric
            
        except Exception as e:
            logger.error(f"Error tracking feedback application: {e}")
            return None
    
    def get_improvement_trends(self, 
                             user_id: str, 
                             task_type: Optional[str] = None,
                             days_back: int = 30) -> Dict[str, Any]:
        """
        Get improvement trends over time for a user
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Filter metrics
            filtered_metrics = [
                m for m in self.impact_metrics 
                if m.user_id == user_id and m.timestamp >= cutoff_date
            ]
            
            if task_type:
                filtered_metrics = [m for m in filtered_metrics if m.task_type == task_type]
            
            if not filtered_metrics:
                return {"message": "No metrics available for the specified period"}
            
            # Calculate trends
            trends = {
                "total_workflows": len(filtered_metrics),
                "average_quality_score": sum(m.response_quality_score for m in filtered_metrics) / len(filtered_metrics),
                "feedback_utilization_rate": len([m for m in filtered_metrics if m.feedback_entries_count > 0]) / len(filtered_metrics),
                "category_improvements": self._calculate_category_improvements(filtered_metrics),
                "time_series_data": self._generate_time_series_data(filtered_metrics),
                "top_improvement_areas": self._identify_top_improvement_areas(filtered_metrics)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating improvement trends: {e}")
            return {"error": str(e)}
    
    def get_feedback_effectiveness_report(self, 
                                        feedback_category: str,
                                        days_back: int = 60) -> Dict[str, Any]:
        """
        Generate a report on the effectiveness of specific feedback categories
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            # Get metrics with this feedback category
            category_metrics = [
                m for m in self.impact_metrics 
                if feedback_category in m.feedback_categories_applied and m.timestamp >= cutoff_date
            ]
            
            # Get metrics without this feedback category for comparison
            no_category_metrics = [
                m for m in self.impact_metrics 
                if feedback_category not in m.feedback_categories_applied and m.timestamp >= cutoff_date
            ]
            
            if not category_metrics:
                return {"message": f"No metrics available for feedback category: {feedback_category}"}
            
            # Calculate effectiveness metrics
            with_feedback_avg = sum(m.response_quality_score for m in category_metrics) / len(category_metrics)
            without_feedback_avg = sum(m.response_quality_score for m in no_category_metrics) / len(no_category_metrics) if no_category_metrics else 0
            
            effectiveness_report = {
                "feedback_category": feedback_category,
                "workflows_with_feedback": len(category_metrics),
                "workflows_without_feedback": len(no_category_metrics),
                "average_quality_with_feedback": with_feedback_avg,
                "average_quality_without_feedback": without_feedback_avg,
                "improvement_delta": with_feedback_avg - without_feedback_avg,
                "effectiveness_percentage": ((with_feedback_avg - without_feedback_avg) / without_feedback_avg * 100) if without_feedback_avg > 0 else 0,
                "most_effective_agents": self._get_most_effective_agents_for_category(category_metrics, feedback_category),
                "improvement_indicators": self._get_category_improvement_indicators(category_metrics, feedback_category)
            }
            
            return effectiveness_report
            
        except Exception as e:
            logger.error(f"Error generating effectiveness report: {e}")
            return {"error": str(e)}
    
    def _calculate_response_quality_score(self, 
                                        response_content: str, 
                                        feedback_categories: List[str],
                                        feedback_entries: List[FeedbackEntry]) -> float:
        """
        Calculate a quality score for the response based on feedback integration
        """
        score = 0.5  # Base score
        
        # Length and structure score (0.2 weight)
        if len(response_content) > 100:
            score += 0.1
        if len(response_content.split('\n')) > 3:  # Multi-paragraph structure
            score += 0.1
        
        # Feedback integration score (0.3 weight)
        for entry in feedback_entries:
            # Check if response addresses feedback points
            if any(keyword.lower() in response_content.lower() for keyword in entry.keywords):
                score += 0.05 * entry.relevance_score
        
        # Category-specific scoring (0.3 weight)
        for category in feedback_categories:
            category_score = self._score_category_adherence(response_content, category)
            score += category_score * 0.1
        
        return min(1.0, score)
    
    def _calculate_improvement_indicators(self, 
                                        response_content: str,
                                        feedback_categories: List[str],
                                        feedback_entries: List[FeedbackEntry]) -> Dict[str, float]:
        """
        Calculate specific improvement indicators based on feedback categories
        """
        indicators = {}
        
        for category in feedback_categories:
            category_indicators = self.improvement_indicators.get(category, [])
            
            for indicator in category_indicators:
                # Calculate indicator score based on content analysis
                indicators[indicator] = self._calculate_indicator_score(
                    response_content, indicator, feedback_entries
                )
        
        return indicators
    
    def _score_category_adherence(self, response_content: str, category: str) -> float:
        """
        Score how well the response adheres to a specific feedback category
        """
        content_lower = response_content.lower()
        
        category_keywords = {
            "presentation_skills": ["clear", "structured", "organized", "concise", "engaging"],
            "technical_accuracy": ["accurate", "verified", "source", "data", "evidence"],
            "business_focus": ["customer", "business", "opportunity", "market", "revenue"],
            "communication_style": ["professional", "appropriate", "audience", "tone"],
            "research_depth": ["comprehensive", "detailed", "analysis", "thorough", "sources"]
        }
        
        keywords = category_keywords.get(category, [])
        matches = sum(1 for keyword in keywords if keyword in content_lower)
        
        return min(1.0, matches / len(keywords)) if keywords else 0.0
    
    def _calculate_indicator_score(self, 
                                 response_content: str, 
                                 indicator: str,
                                 feedback_entries: List[FeedbackEntry]) -> float:
        """
        Calculate score for a specific improvement indicator
        """
        # This is a simplified scoring system - in production, this would be more sophisticated
        content_lower = response_content.lower()
        
        indicator_keywords = {
            "clarity_score": ["clear", "understand", "explain", "clarify"],
            "engagement_score": ["engaging", "interesting", "compelling", "attention"],
            "structure_score": ["organized", "structured", "logical", "flow"],
            "fact_accuracy_score": ["accurate", "verified", "confirmed", "validated"],
            "business_opportunity_identification": ["opportunity", "potential", "market", "growth"],
            "customer_needs_alignment": ["customer", "needs", "requirements", "satisfaction"]
        }
        
        keywords = indicator_keywords.get(indicator, [])
        if not keywords:
            return 0.5  # Default score
        
        matches = sum(1 for keyword in keywords if keyword in content_lower)
        base_score = min(1.0, matches / len(keywords))
        
        # Boost score if relevant feedback was applied
        relevant_feedback = [f for f in feedback_entries if any(k in indicator for k in f.keywords)]
        if relevant_feedback:
            base_score += 0.2 * sum(f.relevance_score for f in relevant_feedback) / len(relevant_feedback)
        
        return min(1.0, base_score)
    
    def _calculate_category_improvements(self, metrics: List[FeedbackImpactMetric]) -> Dict[str, float]:
        """
        Calculate improvement scores by category
        """
        category_improvements = {}
        
        # Group metrics by category
        for metric in metrics:
            for category in metric.feedback_categories_applied:
                if category not in category_improvements:
                    category_improvements[category] = []
                category_improvements[category].append(metric.response_quality_score)
        
        # Calculate average improvement for each category
        for category, scores in category_improvements.items():
            category_improvements[category] = sum(scores) / len(scores)
        
        return category_improvements
    
    def _generate_time_series_data(self, metrics: List[FeedbackImpactMetric]) -> List[Dict[str, Any]]:
        """
        Generate time series data for trend visualization
        """
        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda x: x.timestamp)
        
        time_series = []
        for metric in sorted_metrics:
            time_series.append({
                "timestamp": metric.timestamp.isoformat(),
                "quality_score": metric.response_quality_score,
                "feedback_count": metric.feedback_entries_count,
                "task_type": metric.task_type
            })
        
        return time_series
    
    def _identify_top_improvement_areas(self, metrics: List[FeedbackImpactMetric]) -> List[Dict[str, Any]]:
        """
        Identify areas with the most improvement potential
        """
        category_scores = {}
        
        for metric in metrics:
            for category in metric.feedback_categories_applied:
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(metric.response_quality_score)
        
        # Calculate average scores and identify lowest performing categories
        improvement_areas = []
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            improvement_areas.append({
                "category": category,
                "average_score": avg_score,
                "sample_count": len(scores),
                "improvement_potential": 1.0 - avg_score
            })
        
        # Sort by improvement potential (lowest scores first)
        improvement_areas.sort(key=lambda x: x["average_score"])
        
        return improvement_areas[:5]  # Top 5 improvement areas
    
    def _get_most_effective_agents_for_category(self, 
                                              metrics: List[FeedbackImpactMetric],
                                              category: str) -> List[Dict[str, Any]]:
        """
        Get agents that perform best with specific feedback category
        """
        agent_performance = {}
        
        for metric in metrics:
            if category in metric.feedback_categories_applied:
                for agent in metric.agents_involved:
                    if agent not in agent_performance:
                        agent_performance[agent] = []
                    agent_performance[agent].append(metric.response_quality_score)
        
        # Calculate average performance per agent
        agent_averages = []
        for agent, scores in agent_performance.items():
            agent_averages.append({
                "agent": agent,
                "average_score": sum(scores) / len(scores),
                "sample_count": len(scores)
            })
        
        # Sort by performance
        agent_averages.sort(key=lambda x: x["average_score"], reverse=True)
        
        return agent_averages[:3]  # Top 3 agents
    
    def _get_category_improvement_indicators(self, 
                                           metrics: List[FeedbackImpactMetric],
                                           category: str) -> Dict[str, float]:
        """
        Get improvement indicators for a specific category
        """
        indicators = {}
        indicator_names = self.improvement_indicators.get(category, [])
        
        for indicator in indicator_names:
            scores = []
            for metric in metrics:
                if indicator in metric.improvement_indicators:
                    scores.append(metric.improvement_indicators[indicator])
            
            if scores:
                indicators[indicator] = sum(scores) / len(scores)
        
        return indicators
    
    async def _store_impact_metric(self, metric: FeedbackImpactMetric):
        """
        Store impact metric in Firestore for persistence
        """
        try:
            # Convert to dict for storage
            metric_dict = asdict(metric)
            metric_dict['timestamp'] = metric.timestamp.isoformat()
            
            # Store using existing Firestore function (adapted for impact metrics)
            await store_agent_response(
                content=str(metric_dict),
                user_id=metric.user_id,
                agent_name="FeedbackImpactTracker",
                topic_id=f"impact_metric_{metric.workflow_id}"
            )
            
        except Exception as e:
            logger.error(f"Error storing impact metric: {e}")
