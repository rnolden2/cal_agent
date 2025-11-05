"""
Source reliability tracking system for maintaining source quality over time.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import json

from ..storage.firestore_db import store_agent_response, get_agent_responses

logger = logging.getLogger(__name__)

@dataclass
class SourceReliabilityRecord:
    """Record of source reliability over time"""
    url: str
    domain: str
    reliability_score: float
    verification_count: int
    success_count: int
    failure_count: int
    last_verified: datetime
    first_seen: datetime
    metadata: Dict[str, Any]
    notes: List[str]

@dataclass
class VerificationEvent:
    """Individual verification event for a source"""
    url: str
    timestamp: datetime
    accessible: bool
    reliability_score: float
    response_time: float
    status_code: Optional[int]
    content_quality: float
    verification_context: str

class SourceReliabilityTracker:
    """
    Tracks and scores source reliability over time
    """
    
    def __init__(self):
        self.source_records = {}
        self.verification_events = []
        
        # Pre-defined reliable sources for defense/military content
        self.reliable_sources = {
            # Government sources (highest reliability)
            "darpa.mil": 0.98,
            "army.mil": 0.98,
            "navy.mil": 0.98,
            "af.mil": 0.98,
            "defense.gov": 0.97,
            "dod.mil": 0.97,
            "whitehouse.gov": 0.95,
            "congress.gov": 0.95,
            
            # Defense industry publications
            "defensenews.com": 0.92,
            "janes.com": 0.90,
            "defense-aerospace.com": 0.88,
            "breakingdefense.com": 0.85,
            "militaryaerospace.com": 0.85,
            "c4isrnet.com": 0.83,
            
            # Technical/Academic sources
            "ieee.org": 0.94,
            "spectrum.ieee.org": 0.92,
            "researchgate.net": 0.85,
            "arxiv.org": 0.83,
            
            # Business/Financial sources
            "bloomberg.com": 0.85,
            "reuters.com": 0.88,
            "wsj.com": 0.87,
            "ft.com": 0.86,
            
            # General news sources
            "bbc.com": 0.75,
            "cnn.com": 0.70,
            "npr.org": 0.78,
            "pbs.org": 0.76,
            
            # Industry sources
            "aviationweek.com": 0.82,
            "flightglobal.com": 0.80,
            "spacenews.com": 0.83,
            
            # Educational institutions (general high reliability)
            "mit.edu": 0.90,
            "stanford.edu": 0.90,
            "cmu.edu": 0.88,
            "gatech.edu": 0.87
        }
        
        # Domain reliability patterns
        self.domain_patterns = {
            r'.*\.mil$': 0.95,
            r'.*\.gov$': 0.90,
            r'.*\.edu$': 0.85,
            r'.*\.org$': 0.70,
            r'.*\.com$': 0.60,
            r'.*\.net$': 0.55
        }
        
        # Load existing records
        self._load_source_records()
    
    def get_source_reliability(self, url: str) -> Optional[float]:
        """
        Get reliability score for a source URL
        """
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check pre-defined reliable sources first
            if domain in self.reliable_sources:
                return self.reliable_sources[domain]
            
            # Check tracked records
            if url in self.source_records:
                record = self.source_records[url]
                return record.reliability_score
            
            # Check domain-level records
            domain_records = [r for r in self.source_records.values() if r.domain == domain]
            if domain_records:
                # Average reliability for this domain
                avg_reliability = sum(r.reliability_score for r in domain_records) / len(domain_records)
                return avg_reliability
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting source reliability for {url}: {e}")
            return None
    
    async def update_source_reliability(self, url: str, reliability_score: float, 
                                accessible: bool, response_time: float = 0.0,
                                status_code: Optional[int] = None,
                                content_quality: float = 0.5,
                                context: str = "general") -> None:
        """
        Update reliability information for a source
        """
        try:
            domain = urlparse(url).netloc.lower()
            current_time = datetime.now()
            
            # Create or update source record
            if url not in self.source_records:
                self.source_records[url] = SourceReliabilityRecord(
                    url=url,
                    domain=domain,
                    reliability_score=reliability_score,
                    verification_count=1,
                    success_count=1 if accessible else 0,
                    failure_count=0 if accessible else 1,
                    last_verified=current_time,
                    first_seen=current_time,
                    metadata={},
                    notes=[]
                )
            else:
                record = self.source_records[url]
                record.verification_count += 1
                record.last_verified = current_time
                
                if accessible:
                    record.success_count += 1
                else:
                    record.failure_count += 1
                
                # Update reliability score using weighted average
                # Give more weight to recent performance
                historical_weight = 0.7
                current_weight = 0.3
                record.reliability_score = (
                    record.reliability_score * historical_weight + 
                    reliability_score * current_weight
                )
                
                # Apply success rate adjustment
                success_rate = record.success_count / record.verification_count
                record.reliability_score *= success_rate
                
                # Ensure score stays within bounds
                record.reliability_score = max(0.0, min(1.0, record.reliability_score))
            
            # Record verification event
            event = VerificationEvent(
                url=url,
                timestamp=current_time,
                accessible=accessible,
                reliability_score=reliability_score,
                response_time=response_time,
                status_code=status_code,
                content_quality=content_quality,
                verification_context=context
            )
            
            self.verification_events.append(event)
            
            # Store updated records
            await self._store_source_records()
            
            logger.debug(f"Updated reliability for {url}: {self.source_records[url].reliability_score:.3f}")
            
        except Exception as e:
            logger.error(f"Error updating source reliability for {url}: {e}")
    
    def get_domain_reliability_stats(self, domain: str) -> Dict[str, Any]:
        """
        Get reliability statistics for a domain
        """
        try:
            domain_records = [r for r in self.source_records.values() if r.domain == domain]
            
            if not domain_records:
                return {
                    "domain": domain,
                    "tracked_urls": 0,
                    "average_reliability": None,
                    "total_verifications": 0,
                    "success_rate": None
                }
            
            total_verifications = sum(r.verification_count for r in domain_records)
            total_successes = sum(r.success_count for r in domain_records)
            avg_reliability = sum(r.reliability_score for r in domain_records) / len(domain_records)
            success_rate = total_successes / total_verifications if total_verifications > 0 else 0
            
            return {
                "domain": domain,
                "tracked_urls": len(domain_records),
                "average_reliability": avg_reliability,
                "total_verifications": total_verifications,
                "success_rate": success_rate,
                "most_recent_check": max(r.last_verified for r in domain_records).isoformat(),
                "oldest_record": min(r.first_seen for r in domain_records).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting domain stats for {domain}: {e}")
            return {"error": str(e)}
    
    def get_reliability_trends(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get reliability trends over time
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_events = [e for e in self.verification_events if e.timestamp >= cutoff_date]
            
            if not recent_events:
                return {"message": "No recent verification events found"}
            
            # Group events by day
            daily_stats = {}
            for event in recent_events:
                day_key = event.timestamp.strftime("%Y-%m-%d")
                if day_key not in daily_stats:
                    daily_stats[day_key] = {
                        "total_checks": 0,
                        "successful_checks": 0,
                        "avg_reliability": 0.0,
                        "avg_response_time": 0.0,
                        "unique_domains": set()
                    }
                
                stats = daily_stats[day_key]
                stats["total_checks"] += 1
                if event.accessible:
                    stats["successful_checks"] += 1
                stats["avg_reliability"] += event.reliability_score
                stats["avg_response_time"] += event.response_time
                stats["unique_domains"].add(urlparse(event.url).netloc)
            
            # Calculate averages
            for day_stats in daily_stats.values():
                if day_stats["total_checks"] > 0:
                    day_stats["avg_reliability"] /= day_stats["total_checks"]
                    day_stats["avg_response_time"] /= day_stats["total_checks"]
                day_stats["unique_domains"] = len(day_stats["unique_domains"])
            
            # Overall trends
            total_checks = len(recent_events)
            successful_checks = sum(1 for e in recent_events if e.accessible)
            avg_reliability = sum(e.reliability_score for e in recent_events) / total_checks
            
            return {
                "period_days": days_back,
                "total_verification_events": total_checks,
                "overall_success_rate": successful_checks / total_checks,
                "average_reliability_score": avg_reliability,
                "daily_breakdown": daily_stats,
                "unique_domains_checked": len(set(urlparse(e.url).netloc for e in recent_events))
            }
            
        except Exception as e:
            logger.error(f"Error calculating reliability trends: {e}")
            return {"error": str(e)}
    
    def get_top_reliable_sources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top reliable sources based on historical performance
        """
        try:
            # Filter sources with sufficient verification history
            qualified_sources = [
                r for r in self.source_records.values() 
                if r.verification_count >= 3  # At least 3 verifications
            ]
            
            # Sort by reliability score
            top_sources = sorted(qualified_sources, key=lambda x: x.reliability_score, reverse=True)
            
            result = []
            for record in top_sources[:limit]:
                result.append({
                    "url": record.url,
                    "domain": record.domain,
                    "reliability_score": record.reliability_score,
                    "verification_count": record.verification_count,
                    "success_rate": record.success_count / record.verification_count,
                    "last_verified": record.last_verified.isoformat(),
                    "first_seen": record.first_seen.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting top reliable sources: {e}")
            return []
    
    def get_problematic_sources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get sources with reliability issues
        """
        try:
            # Filter sources with reliability issues
            problematic_sources = [
                r for r in self.source_records.values() 
                if (r.reliability_score < 0.5 or 
                    (r.verification_count >= 3 and r.success_count / r.verification_count < 0.7))
            ]
            
            # Sort by reliability score (lowest first)
            problematic_sources.sort(key=lambda x: x.reliability_score)
            
            result = []
            for record in problematic_sources[:limit]:
                result.append({
                    "url": record.url,
                    "domain": record.domain,
                    "reliability_score": record.reliability_score,
                    "verification_count": record.verification_count,
                    "success_rate": record.success_count / record.verification_count,
                    "failure_count": record.failure_count,
                    "last_verified": record.last_verified.isoformat(),
                    "issues": self._identify_source_issues(record)
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting problematic sources: {e}")
            return []
    
    def _identify_source_issues(self, record: SourceReliabilityRecord) -> List[str]:
        """
        Identify specific issues with a source
        """
        issues = []
        
        success_rate = record.success_count / record.verification_count if record.verification_count > 0 else 0
        
        if success_rate < 0.5:
            issues.append("High failure rate (>50% of checks fail)")
        elif success_rate < 0.7:
            issues.append("Moderate failure rate (30-50% of checks fail)")
        
        if record.reliability_score < 0.3:
            issues.append("Very low reliability score")
        elif record.reliability_score < 0.5:
            issues.append("Low reliability score")
        
        # Check if source hasn't been verified recently
        days_since_check = (datetime.now() - record.last_verified).days
        if days_since_check > 30:
            issues.append(f"Not verified in {days_since_check} days")
        
        if record.failure_count > record.success_count:
            issues.append("More failures than successes")
        
        return issues
    
    def add_source_note(self, url: str, note: str) -> None:
        """
        Add a note to a source record
        """
        try:
            if url in self.source_records:
                self.source_records[url].notes.append(f"{datetime.now().isoformat()}: {note}")
                self._store_source_records()
            else:
                logger.warning(f"Cannot add note to unknown source: {url}")
                
        except Exception as e:
            logger.error(f"Error adding note to source {url}: {e}")
    
    def _load_source_records(self) -> None:
        """
        Load source records from storage
        """
        try:
            # This is a simplified implementation
            # In production, this would load from a dedicated database or file
            logger.info("Source records loaded from memory (simplified implementation)")
            
        except Exception as e:
            logger.error(f"Error loading source records: {e}")
    
    async def _store_source_records(self) -> None:
        """
        Store source records to persistent storage
        """
        try:
            # Store summary statistics
            summary_data = {
                "total_tracked_sources": len(self.source_records),
                "total_verification_events": len(self.verification_events),
                "average_reliability": sum(r.reliability_score for r in self.source_records.values()) / len(self.source_records) if self.source_records else 0,
                "last_updated": datetime.now().isoformat(),
                "top_domains": self._get_top_domains_summary()
            }
            
            await store_agent_response(
                content=json.dumps(summary_data, indent=2),
                user_id="system",
                agent_name="SourceReliabilityTracker",
                topic_id=f"source_summary_{datetime.now().strftime('%Y%m%d')}"
            )
            
            logger.debug("Source records summary stored successfully")
            
        except Exception as e:
            logger.error(f"Error storing source records: {e}")
    
    def _get_top_domains_summary(self) -> Dict[str, Any]:
        """
        Get summary of top domains by reliability
        """
        try:
            domain_stats = {}
            
            for record in self.source_records.values():
                domain = record.domain
                if domain not in domain_stats:
                    domain_stats[domain] = {
                        "url_count": 0,
                        "total_reliability": 0.0,
                        "total_verifications": 0
                    }
                
                stats = domain_stats[domain]
                stats["url_count"] += 1
                stats["total_reliability"] += record.reliability_score
                stats["total_verifications"] += record.verification_count
            
            # Calculate averages and sort
            for domain, stats in domain_stats.items():
                stats["avg_reliability"] = stats["total_reliability"] / stats["url_count"]
            
            # Return top 10 domains by average reliability
            sorted_domains = sorted(
                domain_stats.items(), 
                key=lambda x: x[1]["avg_reliability"], 
                reverse=True
            )
            
            return dict(sorted_domains[:10])
            
        except Exception as e:
            logger.error(f"Error getting top domains summary: {e}")
            return {}
    
    def score_source(self, url: str) -> float:
        """
        Return reliability score for source (legacy method for compatibility)
        """
        score = self.get_source_reliability(url)
        return score if score is not None else 0.5
    
    def get_verification_history(self, url: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get verification history for a specific URL
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            url_events = [
                e for e in self.verification_events 
                if e.url == url and e.timestamp >= cutoff_date
            ]
            
            history = []
            for event in sorted(url_events, key=lambda x: x.timestamp, reverse=True):
                history.append({
                    "timestamp": event.timestamp.isoformat(),
                    "accessible": event.accessible,
                    "reliability_score": event.reliability_score,
                    "response_time": event.response_time,
                    "status_code": event.status_code,
                    "content_quality": event.content_quality,
                    "context": event.verification_context
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting verification history for {url}: {e}")
            return []
