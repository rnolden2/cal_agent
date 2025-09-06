"""
Comprehensive fact verification engine for ensuring accuracy and reliability.
"""

import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
import aiohttp
from bs4 import BeautifulSoup

from .source_tracker import SourceReliabilityTracker
from ..storage.firestore_db import store_agent_response

logger = logging.getLogger(__name__)

@dataclass
class VerificationResult:
    """Result of fact verification process"""
    content: str
    verified_claims: List[Dict[str, Any]]
    unverified_claims: List[Dict[str, Any]]
    verified_sources: List[Dict[str, Any]]
    broken_links: List[str]
    reliability_score: float
    verification_timestamp: datetime
    issues_found: List[str]
    recommendations: List[str]

@dataclass
class ClaimVerification:
    """Individual claim verification result"""
    claim: str
    verified: bool
    confidence_score: float
    supporting_sources: List[str]
    contradicting_sources: List[str]
    verification_method: str
    notes: str

class FactVerificationEngine:
    """
    Comprehensive fact verification system for generated content
    """
    
    def __init__(self):
        self.source_tracker = SourceReliabilityTracker()
        self.verification_cache = {}
        self.cache_expiry = timedelta(hours=24)
        
        # Trusted source patterns for defense/military content
        self.trusted_domains = {
            # Government sources (highest reliability)
            r'.*\.mil$': 0.98,
            r'.*\.gov$': 0.95,
            r'darpa\.mil': 0.98,
            r'army\.mil': 0.98,
            r'navy\.mil': 0.98,
            r'af\.mil': 0.98,
            
            # Defense industry sources
            r'defensenews\.com': 0.92,
            r'janes\.com': 0.90,
            r'defense-aerospace\.com': 0.88,
            r'breakingdefense\.com': 0.85,
            
            # Technical/Academic sources
            r'ieee\.org': 0.94,
            r'.*\.edu$': 0.88,
            r'researchgate\.net': 0.85,
            
            # Business/Industry sources
            r'bloomberg\.com': 0.85,
            r'reuters\.com': 0.88,
            r'wsj\.com': 0.87,
            
            # General news (lower reliability for technical claims)
            r'cnn\.com': 0.70,
            r'bbc\.com': 0.75,
            r'reuters\.com': 0.80
        }
        
        # Claim verification patterns
        self.claim_patterns = {
            'financial': r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|trillion))?',
            'percentage': r'\d+(?:\.\d+)?%',
            'date': r'\b(?:19|20)\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+(?:19|20)\d{2}\b',
            'technical_spec': r'\d+(?:\.\d+)?\s*(?:kW|MW|GW|Hz|kHz|MHz|GHz|V|kV|A|mA|kg|lb|ft|m|km|mph|kph)',
            'company_name': r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*(?:\s+(?:Inc|Corp|LLC|Ltd|Co)\.?)?',
            'program_name': r'\b[A-Z]{2,}(?:-[A-Z0-9]+)*\b'
        }
    
    async def verify_content(self, content: str, context: str = "") -> VerificationResult:
        """
        Comprehensive verification of content including sources and claims
        """
        try:
            logger.info("Starting comprehensive content verification")
            
            # 1. Extract and verify URLs
            urls = self._extract_urls(content)
            url_verification_results = await self._verify_urls(urls)
            
            # 2. Extract and verify claims
            claims = self._extract_claims(content)
            claim_verification_results = await self._verify_claims(claims, url_verification_results['verified_sources'])
            
            # 3. Cross-reference information
            cross_reference_results = await self._cross_reference_information(
                claims, url_verification_results['verified_sources']
            )
            
            # 4. Calculate overall reliability score
            reliability_score = self._calculate_reliability_score(
                url_verification_results, claim_verification_results, cross_reference_results
            )
            
            # 5. Generate recommendations
            recommendations = self._generate_recommendations(
                url_verification_results, claim_verification_results, reliability_score
            )
            
            # 6. Identify issues
            issues = self._identify_issues(
                url_verification_results, claim_verification_results, reliability_score
            )
            
            verification_result = VerificationResult(
                content=content,
                verified_claims=[c for c in claim_verification_results if c.verified],
                unverified_claims=[c for c in claim_verification_results if not c.verified],
                verified_sources=url_verification_results['verified_sources'],
                broken_links=url_verification_results['broken_links'],
                reliability_score=reliability_score,
                verification_timestamp=datetime.now(),
                issues_found=issues,
                recommendations=recommendations
            )
            
            # Store verification result for future reference
            await self._store_verification_result(verification_result, context)
            
            logger.info(f"Content verification completed. Reliability score: {reliability_score:.2f}")
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error in content verification: {e}")
            return VerificationResult(
                content=content,
                verified_claims=[],
                unverified_claims=[],
                verified_sources=[],
                broken_links=[],
                reliability_score=0.0,
                verification_timestamp=datetime.now(),
                issues_found=[f"Verification error: {str(e)}"],
                recommendations=["Manual verification required due to system error"]
            )
    
    async def verify_sources(self, content: str) -> Dict[str, Any]:
        """
        Verify all URLs and sources in content
        """
        try:
            urls = self._extract_urls(content)
            return await self._verify_urls(urls)
            
        except Exception as e:
            logger.error(f"Error verifying sources: {e}")
            return {
                'verified_sources': [],
                'broken_links': [],
                'reliability_scores': {},
                'verification_notes': [f"Error: {str(e)}"]
            }
    
    async def cross_reference_claims(self, claim: str, sources: List[str]) -> bool:
        """
        Verify claims across multiple sources
        """
        try:
            if not sources:
                return False
            
            # Get content from sources
            source_contents = []
            for source in sources:
                try:
                    content = await self._fetch_url_content(source)
                    if content:
                        source_contents.append(content.lower())
                except Exception as e:
                    logger.warning(f"Could not fetch content from {source}: {e}")
                    continue
            
            if not source_contents:
                return False
            
            # Simple claim verification - check if key terms appear in multiple sources
            claim_terms = set(claim.lower().split())
            claim_terms = {term for term in claim_terms if len(term) > 3}  # Filter short words
            
            supporting_sources = 0
            for content in source_contents:
                if any(term in content for term in claim_terms):
                    supporting_sources += 1
            
            # Require at least 2 sources to support the claim
            consensus_threshold = min(2, len(source_contents))
            return supporting_sources >= consensus_threshold
            
        except Exception as e:
            logger.error(f"Error in cross-reference verification: {e}")
            return False
    
    def _extract_urls(self, content: str) -> List[str]:
        """Extract all URLs from content"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        urls = re.findall(url_pattern, content)
        
        # Clean up URLs (remove trailing punctuation)
        cleaned_urls = []
        for url in urls:
            url = url.rstrip('.,;:!?)')
            if url:
                cleaned_urls.append(url)
        
        return list(set(cleaned_urls))  # Remove duplicates
    
    async def _verify_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Verify accessibility and reliability of URLs"""
        verified_sources = []
        broken_links = []
        reliability_scores = {}
        verification_notes = []
        
        if not urls:
            return {
                'verified_sources': verified_sources,
                'broken_links': broken_links,
                'reliability_scores': reliability_scores,
                'verification_notes': ['No URLs found in content']
            }
        
        # Verify URLs concurrently with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def verify_single_url(url: str):
            async with semaphore:
                try:
                    # Check if URL is accessible
                    is_accessible = await self._check_url_accessibility(url)
                    
                    if is_accessible:
                        # Calculate reliability score
                        reliability = self._calculate_source_reliability(url)
                        
                        # Get additional metadata
                        metadata = await self._get_url_metadata(url)
                        
                        verified_sources.append({
                            'url': url,
                            'reliability_score': reliability,
                            'accessible': True,
                            'metadata': metadata,
                            'verified_at': datetime.now().isoformat()
                        })
                        
                        reliability_scores[url] = reliability
                        
                        # Update source tracker
                        self.source_tracker.update_source_reliability(url, reliability, True)
                        
                    else:
                        broken_links.append(url)
                        verification_notes.append(f"Broken link: {url}")
                        
                        # Update source tracker for broken link
                        self.source_tracker.update_source_reliability(url, 0.0, False)
                        
                except Exception as e:
                    logger.warning(f"Error verifying URL {url}: {e}")
                    broken_links.append(url)
                    verification_notes.append(f"Verification error for {url}: {str(e)}")
        
        # Execute URL verification concurrently
        await asyncio.gather(*[verify_single_url(url) for url in urls], return_exceptions=True)
        
        return {
            'verified_sources': verified_sources,
            'broken_links': broken_links,
            'reliability_scores': reliability_scores,
            'verification_notes': verification_notes
        }
    
    async def _check_url_accessibility(self, url: str) -> bool:
        """Check if URL is accessible"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.head(url, allow_redirects=True) as response:
                    return response.status < 400
                    
        except Exception as e:
            logger.debug(f"URL accessibility check failed for {url}: {e}")
            return False
    
    async def _fetch_url_content(self, url: str) -> Optional[str]:
        """Fetch content from URL for analysis"""
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status < 400:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract text content
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        text = soup.get_text()
                        return ' '.join(text.split())  # Clean whitespace
                    
        except Exception as e:
            logger.debug(f"Content fetch failed for {url}: {e}")
            
        return None
    
    async def _get_url_metadata(self, url: str) -> Dict[str, Any]:
        """Get metadata about the URL"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status < 400:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        metadata = {
                            'title': '',
                            'description': '',
                            'domain': urlparse(url).netloc,
                            'content_type': response.headers.get('content-type', ''),
                            'last_modified': response.headers.get('last-modified', ''),
                            'status_code': response.status
                        }
                        
                        # Extract title
                        title_tag = soup.find('title')
                        if title_tag:
                            metadata['title'] = title_tag.get_text().strip()
                        
                        # Extract description
                        desc_tag = soup.find('meta', attrs={'name': 'description'})
                        if desc_tag:
                            metadata['description'] = desc_tag.get('content', '').strip()
                        
                        return metadata
                        
        except Exception as e:
            logger.debug(f"Metadata extraction failed for {url}: {e}")
        
        return {
            'domain': urlparse(url).netloc,
            'error': 'Could not extract metadata'
        }
    
    def _calculate_source_reliability(self, url: str) -> float:
        """Calculate reliability score for a source URL"""
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check against trusted domain patterns
            for pattern, score in self.trusted_domains.items():
                if re.match(pattern, domain):
                    return score
            
            # Check historical reliability from source tracker
            historical_score = self.source_tracker.get_source_reliability(url)
            if historical_score is not None:
                return historical_score
            
            # Default scoring based on domain characteristics
            if '.edu' in domain or '.gov' in domain or '.mil' in domain:
                return 0.85
            elif any(keyword in domain for keyword in ['defense', 'military', 'ieee', 'research']):
                return 0.75
            elif any(keyword in domain for keyword in ['news', 'media', 'press']):
                return 0.65
            else:
                return 0.50  # Unknown sources get moderate score
                
        except Exception as e:
            logger.warning(f"Error calculating source reliability for {url}: {e}")
            return 0.50
    
    def _extract_claims(self, content: str) -> List[str]:
        """Extract factual claims from content"""
        claims = []
        
        # Split content into sentences
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
            
            # Check if sentence contains factual patterns
            has_factual_content = False
            
            for pattern_type, pattern in self.claim_patterns.items():
                if re.search(pattern, sentence):
                    has_factual_content = True
                    break
            
            # Also check for factual indicators
            factual_indicators = [
                'according to', 'reported', 'announced', 'stated', 'confirmed',
                'research shows', 'study found', 'data indicates', 'statistics show',
                'awarded', 'contracted', 'developed', 'launched', 'tested'
            ]
            
            if any(indicator in sentence.lower() for indicator in factual_indicators):
                has_factual_content = True
            
            if has_factual_content:
                claims.append(sentence)
        
        return claims
    
    async def _verify_claims(self, claims: List[str], verified_sources: List[Dict[str, Any]]) -> List[ClaimVerification]:
        """Verify individual claims against sources"""
        claim_verifications = []
        
        for claim in claims:
            try:
                # Simple verification - check if claim elements appear in source content
                verification = await self._verify_single_claim(claim, verified_sources)
                claim_verifications.append(verification)
                
            except Exception as e:
                logger.warning(f"Error verifying claim '{claim[:50]}...': {e}")
                claim_verifications.append(ClaimVerification(
                    claim=claim,
                    verified=False,
                    confidence_score=0.0,
                    supporting_sources=[],
                    contradicting_sources=[],
                    verification_method="error",
                    notes=f"Verification error: {str(e)}"
                ))
        
        return claim_verifications
    
    async def _verify_single_claim(self, claim: str, verified_sources: List[Dict[str, Any]]) -> ClaimVerification:
        """Verify a single claim against available sources"""
        supporting_sources = []
        contradicting_sources = []
        confidence_score = 0.0
        
        if not verified_sources:
            return ClaimVerification(
                claim=claim,
                verified=False,
                confidence_score=0.0,
                supporting_sources=[],
                contradicting_sources=[],
                verification_method="no_sources",
                notes="No verified sources available for cross-reference"
            )
        
        # Extract key terms from claim
        claim_terms = self._extract_key_terms(claim)
        
        # Check each source
        for source in verified_sources:
            try:
                source_content = await self._fetch_url_content(source['url'])
                if source_content:
                    # Simple term matching (in production, this would be more sophisticated)
                    matches = sum(1 for term in claim_terms if term.lower() in source_content.lower())
                    match_ratio = matches / len(claim_terms) if claim_terms else 0
                    
                    if match_ratio > 0.5:  # More than half the terms match
                        supporting_sources.append(source['url'])
                        confidence_score += source['reliability_score'] * match_ratio
                    
            except Exception as e:
                logger.debug(f"Error checking claim against source {source['url']}: {e}")
                continue
        
        # Normalize confidence score
        if supporting_sources:
            confidence_score = min(1.0, confidence_score / len(supporting_sources))
        
        verified = confidence_score > 0.6 and len(supporting_sources) >= 1
        
        return ClaimVerification(
            claim=claim,
            verified=verified,
            confidence_score=confidence_score,
            supporting_sources=supporting_sources,
            contradicting_sources=contradicting_sources,
            verification_method="term_matching",
            notes=f"Matched {len(supporting_sources)} sources with confidence {confidence_score:.2f}"
        )
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text for verification"""
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        # Extract words and numbers
        terms = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out stop words and short terms
        key_terms = [term for term in terms if term not in stop_words and len(term) > 2]
        
        # Also extract specific patterns (numbers, dates, etc.)
        for pattern in self.claim_patterns.values():
            matches = re.findall(pattern, text)
            key_terms.extend(matches)
        
        return list(set(key_terms))  # Remove duplicates
    
    async def _cross_reference_information(self, claims: List[str], verified_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Cross-reference information across multiple sources"""
        cross_reference_results = {
            'consensus_claims': [],
            'conflicting_claims': [],
            'single_source_claims': [],
            'cross_reference_score': 0.0
        }
        
        # This is a simplified implementation
        # In production, this would involve more sophisticated NLP and fact-checking
        
        for claim in claims:
            supporting_count = 0
            for source in verified_sources:
                if await self.cross_reference_claims(claim, [source['url']]):
                    supporting_count += 1
            
            if supporting_count >= 2:
                cross_reference_results['consensus_claims'].append(claim)
            elif supporting_count == 1:
                cross_reference_results['single_source_claims'].append(claim)
            else:
                cross_reference_results['conflicting_claims'].append(claim)
        
        # Calculate cross-reference score
        total_claims = len(claims)
        if total_claims > 0:
            consensus_ratio = len(cross_reference_results['consensus_claims']) / total_claims
            single_source_ratio = len(cross_reference_results['single_source_claims']) / total_claims
            cross_reference_results['cross_reference_score'] = consensus_ratio + (single_source_ratio * 0.5)
        
        return cross_reference_results
    
    def _calculate_reliability_score(self, 
                                   url_results: Dict[str, Any], 
                                   claim_results: List[ClaimVerification],
                                   cross_ref_results: Dict[str, Any]) -> float:
        """Calculate overall reliability score for content"""
        try:
            scores = []
            
            # Source reliability score (40% weight)
            if url_results['verified_sources']:
                source_scores = [s['reliability_score'] for s in url_results['verified_sources']]
                avg_source_score = sum(source_scores) / len(source_scores)
                scores.append(('source_reliability', avg_source_score, 0.4))
            else:
                scores.append(('source_reliability', 0.0, 0.4))
            
            # Claim verification score (35% weight)
            if claim_results:
                verified_claims = [c for c in claim_results if c.verified]
                claim_score = len(verified_claims) / len(claim_results)
                scores.append(('claim_verification', claim_score, 0.35))
            else:
                scores.append(('claim_verification', 0.5, 0.35))  # Neutral if no claims
            
            # Cross-reference score (25% weight)
            cross_ref_score = cross_ref_results.get('cross_reference_score', 0.0)
            scores.append(('cross_reference', cross_ref_score, 0.25))
            
            # Calculate weighted average
            total_score = sum(score * weight for _, score, weight in scores)
            
            # Apply penalties for issues
            if url_results['broken_links']:
                penalty = min(0.2, len(url_results['broken_links']) * 0.05)
                total_score -= penalty
            
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating reliability score: {e}")
            return 0.0
    
    def _generate_recommendations(self, 
                                url_results: Dict[str, Any],
                                claim_results: List[ClaimVerification],
                                reliability_score: float) -> List[str]:
        """Generate recommendations for improving content reliability"""
        recommendations = []
        
        if reliability_score < 0.7:
            recommendations.append("Content reliability is below acceptable threshold. Consider additional verification.")
        
        if url_results['broken_links']:
            recommendations.append(f"Fix {len(url_results['broken_links'])} broken links to improve source reliability.")
        
        unverified_claims = [c for c in claim_results if not c.verified]
        if unverified_claims:
            recommendations.append(f"Verify {len(unverified_claims)} unverified claims with additional sources.")
        
        low_reliability_sources = [s for s in url_results['verified_sources'] if s['reliability_score'] < 0.6]
        if low_reliability_sources:
            recommendations.append(f"Consider replacing {len(low_reliability_sources)} low-reliability sources with more authoritative ones.")
        
        if not url_results['verified_sources']:
            recommendations.append("Add credible sources to support the claims made in the content.")
        
        if len(url_results['verified_sources']) < 3:
            recommendations.append("Consider adding more sources for better cross-verification.")
        
        return recommendations
    
    def _identify_issues(self, 
                        url_results: Dict[str, Any],
                        claim_results: List[ClaimVerification],
                        reliability_score: float) -> List[str]:
        """Identify specific issues with the content"""
        issues = []
        
        if url_results['broken_links']:
            issues.extend([f"Broken link: {link}" for link in url_results['broken_links']])
        
        unverified_claims = [c for c in claim_results if not c.verified and c.confidence_score < 0.3]
        for claim in unverified_claims:
            issues.append(f"Unverified claim: {claim.claim[:100]}...")
        
        if reliability_score < 0.5:
            issues.append("Overall content reliability is critically low")
        elif reliability_score < 0.7:
            issues.append("Content reliability is below recommended threshold")
        
        return issues
    
    async def _store_verification_result(self, result: VerificationResult, context: str):
        """Store verification result for future reference"""
        try:
            verification_data = {
                'reliability_score': result.reliability_score,
                'verified_claims_count': len(result.verified_claims),
                'unverified_claims_count': len(result.unverified_claims),
                'verified_sources_count': len(result.verified_sources),
                'broken_links_count': len(result.broken_links),
                'issues_count': len(result.issues_found),
                'timestamp': result.verification_timestamp.isoformat(),
                'context': context
            }
            
            await store_agent_response(
                content=str(verification_data),
                user_id="system",
                agent_name="FactVerificationEngine",
                topic_id=f"verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
        except Exception as e:
            logger.error(f"Error storing verification result: {e}")
