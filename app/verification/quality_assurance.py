"""
Quality assurance system for ensuring content meets reliability standards.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from .fact_verifier import FactVerificationEngine, VerificationResult
from .source_tracker import SourceReliabilityTracker

logger = logging.getLogger(__name__)

@dataclass
class QualityAssessment:
    """Quality assessment result for content"""
    content: str
    overall_quality_score: float
    verification_result: VerificationResult
    quality_issues: List[str]
    quality_recommendations: List[str]
    approval_status: str  # "approved", "needs_review", "rejected"
    assessment_timestamp: datetime
    quality_metrics: Dict[str, float]

class QualityAssuranceSystem:
    """
    Comprehensive quality assurance system for generated content
    """
    
    def __init__(self):
        self.fact_verifier = FactVerificationEngine()
        self.source_tracker = SourceReliabilityTracker()
        
        # Quality thresholds
        self.quality_thresholds = {
            "minimum_reliability_score": 0.7,
            "minimum_source_count": 2,
            "maximum_broken_links": 0,
            "minimum_verified_claims_ratio": 0.8,
            "minimum_overall_quality": 0.75
        }
        
        # Quality metrics weights
        self.quality_weights = {
            "source_reliability": 0.30,
            "claim_verification": 0.25,
            "content_structure": 0.15,
            "factual_accuracy": 0.20,
            "source_diversity": 0.10
        }
    
    async def assess_content_quality(self, content: str, context: str = "") -> QualityAssessment:
        """
        Comprehensive quality assessment of content
        """
        try:
            logger.info("Starting comprehensive quality assessment")
            
            # 1. Perform fact verification
            verification_result = await self.fact_verifier.verify_content(content, context)
            
            # 2. Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(content, verification_result)
            
            # 3. Calculate overall quality score
            overall_quality_score = self._calculate_overall_quality_score(quality_metrics)
            
            # 4. Identify quality issues
            quality_issues = self._identify_quality_issues(verification_result, quality_metrics)
            
            # 5. Generate quality recommendations
            quality_recommendations = self._generate_quality_recommendations(
                verification_result, quality_metrics, quality_issues
            )
            
            # 6. Determine approval status
            approval_status = self._determine_approval_status(
                overall_quality_score, quality_issues, verification_result
            )
            
            assessment = QualityAssessment(
                content=content,
                overall_quality_score=overall_quality_score,
                verification_result=verification_result,
                quality_issues=quality_issues,
                quality_recommendations=quality_recommendations,
                approval_status=approval_status,
                assessment_timestamp=datetime.now(),
                quality_metrics=quality_metrics
            )
            
            logger.info(f"Quality assessment completed. Overall score: {overall_quality_score:.2f}, Status: {approval_status}")
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error in quality assessment: {e}")
            return QualityAssessment(
                content=content,
                overall_quality_score=0.0,
                verification_result=VerificationResult(
                    content=content,
                    verified_claims=[],
                    unverified_claims=[],
                    verified_sources=[],
                    broken_links=[],
                    reliability_score=0.0,
                    verification_timestamp=datetime.now(),
                    issues_found=[f"Quality assessment error: {str(e)}"],
                    recommendations=["Manual review required due to system error"]
                ),
                quality_issues=[f"Assessment error: {str(e)}"],
                quality_recommendations=["Manual quality review required"],
                approval_status="needs_review",
                assessment_timestamp=datetime.now(),
                quality_metrics={}
            )
    
    def _calculate_quality_metrics(self, content: str, verification_result: VerificationResult) -> Dict[str, float]:
        """
        Calculate detailed quality metrics
        """
        metrics = {}
        
        try:
            # Source reliability metric
            if verification_result.verified_sources:
                avg_source_reliability = sum(
                    s['reliability_score'] for s in verification_result.verified_sources
                ) / len(verification_result.verified_sources)
                metrics["source_reliability"] = avg_source_reliability
            else:
                metrics["source_reliability"] = 0.0
            
            # Claim verification metric
            total_claims = len(verification_result.verified_claims) + len(verification_result.unverified_claims)
            if total_claims > 0:
                verified_ratio = len(verification_result.verified_claims) / total_claims
                metrics["claim_verification"] = verified_ratio
            else:
                metrics["claim_verification"] = 1.0  # No claims to verify
            
            # Content structure metric
            metrics["content_structure"] = self._assess_content_structure(content)
            
            # Factual accuracy metric (based on verification result)
            metrics["factual_accuracy"] = verification_result.reliability_score
            
            # Source diversity metric
            metrics["source_diversity"] = self._assess_source_diversity(verification_result.verified_sources)
            
            # Additional metrics
            metrics["broken_links_penalty"] = max(0.0, 1.0 - (len(verification_result.broken_links) * 0.1))
            metrics["issue_penalty"] = max(0.0, 1.0 - (len(verification_result.issues_found) * 0.05))
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            # Return default metrics
            metrics = {
                "source_reliability": 0.0,
                "claim_verification": 0.0,
                "content_structure": 0.0,
                "factual_accuracy": 0.0,
                "source_diversity": 0.0,
                "broken_links_penalty": 0.0,
                "issue_penalty": 0.0
            }
        
        return metrics
    
    def _assess_content_structure(self, content: str) -> float:
        """
        Assess the structural quality of content
        """
        try:
            score = 0.0
            
            # Length assessment
            if len(content) > 100:
                score += 0.2
            if len(content) > 500:
                score += 0.1
            
            # Paragraph structure
            paragraphs = content.split('\n\n')
            if len(paragraphs) > 1:
                score += 0.2
            
            # Sentence structure
            sentences = content.split('.')
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            if 10 <= avg_sentence_length <= 25:  # Optimal sentence length
                score += 0.2
            
            # Headers/sections (simple detection)
            if any(line.strip().isupper() or line.startswith('#') for line in content.split('\n')):
                score += 0.1
            
            # Lists or bullet points
            if any(line.strip().startswith(('•', '-', '*', '1.', '2.')) for line in content.split('\n')):
                score += 0.1
            
            # Professional language indicators
            professional_indicators = ['according to', 'research shows', 'data indicates', 'analysis reveals']
            if any(indicator in content.lower() for indicator in professional_indicators):
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error assessing content structure: {e}")
            return 0.5
    
    def _assess_source_diversity(self, verified_sources: List[Dict[str, Any]]) -> float:
        """
        Assess diversity of sources used
        """
        try:
            if not verified_sources:
                return 0.0
            
            # Count unique domains
            domains = set()
            source_types = set()
            
            for source in verified_sources:
                domain = source.get('metadata', {}).get('domain', '')
                domains.add(domain)
                
                # Categorize source types
                if any(ext in domain for ext in ['.gov', '.mil']):
                    source_types.add('government')
                elif '.edu' in domain:
                    source_types.add('academic')
                elif any(keyword in domain for keyword in ['news', 'media']):
                    source_types.add('news')
                elif any(keyword in domain for keyword in ['ieee', 'research']):
                    source_types.add('technical')
                else:
                    source_types.add('other')
            
            # Score based on diversity
            domain_diversity = min(1.0, len(domains) / 5)  # Optimal: 5+ different domains
            type_diversity = min(1.0, len(source_types) / 3)  # Optimal: 3+ different types
            
            return (domain_diversity + type_diversity) / 2
            
        except Exception as e:
            logger.error(f"Error assessing source diversity: {e}")
            return 0.5
    
    def _calculate_overall_quality_score(self, quality_metrics: Dict[str, float]) -> float:
        """
        Calculate overall quality score using weighted metrics
        """
        try:
            weighted_score = 0.0
            
            for metric, weight in self.quality_weights.items():
                if metric in quality_metrics:
                    weighted_score += quality_metrics[metric] * weight
            
            # Apply penalties
            penalties = quality_metrics.get("broken_links_penalty", 1.0) * quality_metrics.get("issue_penalty", 1.0)
            weighted_score *= penalties
            
            return max(0.0, min(1.0, weighted_score))
            
        except Exception as e:
            logger.error(f"Error calculating overall quality score: {e}")
            return 0.0
    
    def _identify_quality_issues(self, verification_result: VerificationResult, 
                               quality_metrics: Dict[str, float]) -> List[str]:
        """
        Identify specific quality issues
        """
        issues = []
        
        try:
            # Source-related issues
            if quality_metrics.get("source_reliability", 0) < self.quality_thresholds["minimum_reliability_score"]:
                issues.append("Source reliability below acceptable threshold")
            
            if len(verification_result.verified_sources) < self.quality_thresholds["minimum_source_count"]:
                issues.append(f"Insufficient sources (minimum {self.quality_thresholds['minimum_source_count']} required)")
            
            if len(verification_result.broken_links) > self.quality_thresholds["maximum_broken_links"]:
                issues.append(f"Contains {len(verification_result.broken_links)} broken links")
            
            # Claim verification issues
            total_claims = len(verification_result.verified_claims) + len(verification_result.unverified_claims)
            if total_claims > 0:
                verified_ratio = len(verification_result.verified_claims) / total_claims
                if verified_ratio < self.quality_thresholds["minimum_verified_claims_ratio"]:
                    issues.append(f"Too many unverified claims ({len(verification_result.unverified_claims)} unverified)")
            
            # Content structure issues
            if quality_metrics.get("content_structure", 0) < 0.5:
                issues.append("Poor content structure and organization")
            
            # Source diversity issues
            if quality_metrics.get("source_diversity", 0) < 0.3:
                issues.append("Limited source diversity")
            
            # Add issues from verification result
            issues.extend(verification_result.issues_found)
            
        except Exception as e:
            logger.error(f"Error identifying quality issues: {e}")
            issues.append(f"Error in quality assessment: {str(e)}")
        
        return issues
    
    def _generate_quality_recommendations(self, verification_result: VerificationResult,
                                        quality_metrics: Dict[str, float],
                                        quality_issues: List[str]) -> List[str]:
        """
        Generate recommendations for improving content quality
        """
        recommendations = []
        
        try:
            # Source improvement recommendations
            if quality_metrics.get("source_reliability", 0) < 0.7:
                recommendations.append("Add more authoritative sources (government, academic, or industry publications)")
            
            if len(verification_result.verified_sources) < 3:
                recommendations.append("Include additional credible sources for better verification")
            
            if verification_result.broken_links:
                recommendations.append("Fix or replace broken links with working alternatives")
            
            # Content improvement recommendations
            if quality_metrics.get("content_structure", 0) < 0.6:
                recommendations.append("Improve content structure with clear headings, paragraphs, and logical flow")
            
            if quality_metrics.get("source_diversity", 0) < 0.4:
                recommendations.append("Diversify sources across different types (government, academic, industry, news)")
            
            # Claim verification recommendations
            if len(verification_result.unverified_claims) > 0:
                recommendations.append(f"Verify {len(verification_result.unverified_claims)} unverified claims with additional sources")
            
            # Add recommendations from verification result
            recommendations.extend(verification_result.recommendations)
            
            # General recommendations based on overall score
            overall_score = self._calculate_overall_quality_score(quality_metrics)
            if overall_score < 0.6:
                recommendations.append("Consider comprehensive revision to meet quality standards")
            elif overall_score < 0.8:
                recommendations.append("Minor improvements needed to reach optimal quality")
            
        except Exception as e:
            logger.error(f"Error generating quality recommendations: {e}")
            recommendations.append("Manual quality review recommended due to system error")
        
        return recommendations
    
    def _determine_approval_status(self, overall_quality_score: float, 
                                 quality_issues: List[str],
                                 verification_result: VerificationResult) -> str:
        """
        Determine approval status based on quality assessment
        """
        try:
            # Critical issues that require rejection
            critical_issues = [
                "broken links",
                "very low reliability",
                "critically low",
                "verification error"
            ]
            
            has_critical_issues = any(
                any(critical in issue.lower() for critical in critical_issues)
                for issue in quality_issues
            )
            
            if has_critical_issues:
                return "rejected"
            
            # Quality score thresholds
            if overall_quality_score >= self.quality_thresholds["minimum_overall_quality"]:
                # Additional checks for approval
                if (verification_result.reliability_score >= self.quality_thresholds["minimum_reliability_score"] and
                    len(verification_result.broken_links) <= self.quality_thresholds["maximum_broken_links"]):
                    return "approved"
                else:
                    return "needs_review"
            elif overall_quality_score >= 0.5:
                return "needs_review"
            else:
                return "rejected"
                
        except Exception as e:
            logger.error(f"Error determining approval status: {e}")
            return "needs_review"
    
    def get_quality_standards(self) -> Dict[str, Any]:
        """
        Get current quality standards and thresholds
        """
        return {
            "quality_thresholds": self.quality_thresholds,
            "quality_weights": self.quality_weights,
            "description": {
                "minimum_reliability_score": "Minimum average reliability score for sources",
                "minimum_source_count": "Minimum number of verified sources required",
                "maximum_broken_links": "Maximum number of broken links allowed",
                "minimum_verified_claims_ratio": "Minimum ratio of verified to total claims",
                "minimum_overall_quality": "Minimum overall quality score for approval"
            }
        }
    
    def update_quality_standards(self, new_thresholds: Dict[str, float]) -> bool:
        """
        Update quality standards (for administrative use)
        """
        try:
            for key, value in new_thresholds.items():
                if key in self.quality_thresholds and 0.0 <= value <= 1.0:
                    self.quality_thresholds[key] = value
                    logger.info(f"Updated quality threshold {key} to {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating quality standards: {e}")
            return False
