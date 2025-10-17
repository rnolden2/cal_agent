"""
Feedback file processor for parsing and tagging uploaded txt files.
Converts raw feedback text into structured entries for LLM use.
"""

import logging
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import asyncio

from ..context.relevance_scorer import RelevanceScorer, FeedbackEntry
from ..storage.cloud_storage import FeedbackCloudStorage

logger = logging.getLogger(__name__)

class FeedbackFileProcessor:
    """
    Processes uploaded feedback txt files into structured, tagged entries.
    Handles parsing, categorization, and tagging for efficient LLM integration.
    """
    
    def __init__(self):
        self.relevance_scorer = RelevanceScorer()
        self.cloud_storage = FeedbackCloudStorage()
        
        # Feedback categories for auto-classification
        self.category_keywords = {
            "presentation_skills": [
                "presentation", "tone", "cadence", "verbose", "concise", "clarity",
                "speaking", "delivery", "pitch", "audience", "visual", "slide"
            ],
            "technical_accuracy": [
                "technical", "accuracy", "specification", "engineering", "data",
                "calculation", "measurement", "precise", "correct", "exact"
            ],
            "business_focus": [
                "business", "customer", "revenue", "opportunity", "market",
                "profit", "cost", "value", "strategy", "commercial"
            ],
            "communication_style": [
                "communication", "explain", "clarity", "understand", "clear",
                "simple", "complex", "jargon", "language", "style"
            ],
            "research_depth": [
                "research", "data", "analysis", "elaborate", "detail", "depth",
                "thorough", "comprehensive", "investigate", "sources"
            ],
            "general": [
                "feedback", "improve", "better", "suggestion", "recommend",
                "should", "could", "need", "more", "less"
            ]
        }
    
    def _categorize_feedback_text(self, text: str) -> str:
        """
        Automatically categorize feedback text based on keywords.
        
        Args:
            text: The feedback text to categorize
            
        Returns:
            Category name
        """
        text_lower = text.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            # Return category with highest score
            return max(category_scores, key=category_scores.get)
        
        return "general"
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from feedback text for tagging.
        
        Args:
            text: The text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords
        """
        # Clean and normalize text
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Split into words and filter
        words = text_clean.split()
        meaningful_words = [
            word for word in words 
            if len(word) > 2 and word not in stop_words and word.isalpha()
        ]
        
        # Count word frequency
        word_freq = {}
        for word in meaningful_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Extract multi-word phrases (2-3 words)
        phrases = []
        for i in range(len(meaningful_words) - 1):
            if i < len(meaningful_words) - 2:
                # 3-word phrases
                phrase = ' '.join(meaningful_words[i:i+3])
                if len(phrase) > 10:
                    phrases.append(phrase)
            
            # 2-word phrases
            phrase = ' '.join(meaningful_words[i:i+2])
            if len(phrase) > 6:
                phrases.append(phrase)
        
        # Count phrase frequency
        phrase_freq = {}
        for phrase in phrases:
            phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1
        
        # Combine and sort by frequency
        all_keywords = []
        
        # Add top single words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        all_keywords.extend([word for word, freq in sorted_words[:max_keywords//2]])
        
        # Add top phrases
        sorted_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)
        all_keywords.extend([phrase for phrase, freq in sorted_phrases[:max_keywords//2]])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in all_keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:max_keywords]
    
    def _parse_feedback_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse feedback text into individual sections/entries.
        
        Args:
            text: The full feedback text
            
        Returns:
            List of parsed feedback sections
        """
        # Split by common section delimiters
        section_patterns = [
            r'\n\s*[-=]{3,}\s*\n',  # Horizontal lines
            r'\n\s*\d+\.\s*',       # Numbered lists
            r'\n\s*[•·*]\s*',       # Bullet points
            r'\n\s*[A-Z][^.!?]*[.!?]\s*\n', # Complete sentences on their own lines
        ]
        
        sections = [text]  # Start with full text
        
        for pattern in section_patterns:
            new_sections = []
            for section in sections:
                parts = re.split(pattern, section)
                new_sections.extend([part.strip() for part in parts if part.strip()])
            sections = new_sections
        
        # Filter out very short sections
        meaningful_sections = []
        for section in sections:
            if len(section.strip()) > 20:  # Minimum meaningful length
                meaningful_sections.append(section.strip())
        
        # If we have too few sections, try to split by paragraphs
        if len(meaningful_sections) < 2 and len(text) > 200:
            paragraphs = text.split('\n\n')
            meaningful_sections = [p.strip() for p in paragraphs if len(p.strip()) > 20]
        
        # Convert to structured format
        parsed_sections = []
        for i, section in enumerate(meaningful_sections):
            category = self._categorize_feedback_text(section)
            keywords = self._extract_keywords(section, max_keywords=5)
            
            parsed_sections.append({
                "section_id": i + 1,
                "content": section,
                "category": category,
                "keywords": keywords,
                "length": len(section),
                "timestamp": datetime.now().isoformat()
            })
        
        return parsed_sections
    
    async def process_feedback_file(self, file_id: str) -> Dict[str, Any]:
        """
        Process an uploaded feedback file into structured entries.
        
        Args:
            file_id: The ID of the uploaded file to process
            
        Returns:
            Dict containing processing results
        """
        try:
            # Get the file from cloud storage
            file_info = await self.cloud_storage.get_feedback_file(file_id)
            if not file_info:
                return {
                    "success": False,
                    "error": f"File {file_id} not found",
                    "file_id": file_id
                }
            
            content = file_info["content"]
            metadata = file_info["metadata"]
            
            logger.info(f"Processing feedback file: {file_id}")
            
            # Parse content into sections
            sections = self._parse_feedback_sections(content)
            
            # Convert sections to FeedbackEntry objects for consistency
            feedback_entries = []
            all_keywords = set()
            
            for section in sections:
                entry = FeedbackEntry(
                    content=section["content"],
                    category=section["category"],
                    timestamp=datetime.now(),
                    source="uploaded_file",
                    context=f"File: {metadata.get('original_filename', 'unknown')}",
                    keywords=section["keywords"]
                )
                feedback_entries.append(entry)
                all_keywords.update(section["keywords"])
            
            # Generate overall file tags
            file_keywords = self._extract_keywords(content, max_keywords=15)
            dominant_category = max(
                set(entry.category for entry in feedback_entries),
                key=lambda cat: sum(1 for entry in feedback_entries if entry.category == cat)
            )
            
            file_tags = [dominant_category] + file_keywords[:10]
            
            # Create processed content structure
            processed_content = {
                "file_id": file_id,
                "original_filename": metadata.get("original_filename"),
                "processed_timestamp": datetime.now().isoformat(),
                "processing_version": "1.0",
                "total_sections": len(sections),
                "dominant_category": dominant_category,
                "file_tags": file_tags,
                "sections": sections,
                "feedback_entries": [
                    {
                        "content": entry.content,
                        "category": entry.category,
                        "timestamp": entry.timestamp.isoformat(),
                        "source": entry.source,
                        "context": entry.context,
                        "keywords": entry.keywords
                    }
                    for entry in feedback_entries
                ],
                "statistics": {
                    "total_length": len(content),
                    "sections_count": len(sections),
                    "categories": list(set(entry.category for entry in feedback_entries)),
                    "unique_keywords": list(all_keywords),
                    "avg_section_length": sum(s["length"] for s in sections) / len(sections) if sections else 0
                }
            }
            
            # Store processed file
            processed_json = json.dumps(processed_content, indent=2)
            processing_metadata = {
                "original_user_id": metadata.get("user_id"),
                "sections_count": len(sections),
                "dominant_category": dominant_category,
                "total_length": len(content)
            }
            
            success = await self.cloud_storage.store_processed_file(
                file_id=file_id,
                processed_content=processed_json,
                tags=file_tags,
                metadata=processing_metadata
            )
            
            if success:
                logger.info(f"Successfully processed feedback file: {file_id} ({len(sections)} sections)")
                return {
                    "success": True,
                    "file_id": file_id,
                    "sections_count": len(sections),
                    "dominant_category": dominant_category,
                    "file_tags": file_tags,
                    "processed_content": processed_content
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store processed file",
                    "file_id": file_id
                }
            
        except Exception as e:
            logger.error(f"Error processing feedback file {file_id}: {e}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "file_id": file_id
            }
    
    async def batch_process_files(self, file_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple feedback files in batch.
        
        Args:
            file_ids: List of file IDs to process
            
        Returns:
            List of processing results
        """
        results = []
        
        for file_id in file_ids:
            try:
                result = await self.process_feedback_file(file_id)
                results.append(result)
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in batch processing file {file_id}: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "file_id": file_id
                })
        
        return results
    
    async def get_processed_feedback_entries(self) -> List[FeedbackEntry]:
        """
        Load all processed feedback files and convert to FeedbackEntry objects.
        
        Returns:
            List of FeedbackEntry objects from all processed files
        """
        try:
            processed_files = await self.cloud_storage.list_processed_files()
            all_entries = []
            
            for file_info in processed_files:
                try:
                    content_json = await self.cloud_storage.get_processed_file_content(
                        file_info["filename"]
                    )
                    
                    if content_json:
                        content_data = json.loads(content_json)
                        
                        # Convert stored feedback entries back to FeedbackEntry objects
                        for entry_data in content_data.get("feedback_entries", []):
                            entry = FeedbackEntry(
                                content=entry_data["content"],
                                category=entry_data["category"],
                                timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                                source=entry_data.get("source", "uploaded_file"),
                                context=entry_data.get("context", ""),
                                keywords=entry_data.get("keywords", [])
                            )
                            all_entries.append(entry)
                
                except Exception as e:
                    logger.error(f"Error loading processed file {file_info['filename']}: {e}")
                    continue
            
            logger.info(f"Loaded {len(all_entries)} feedback entries from {len(processed_files)} processed files")
            return all_entries
            
        except Exception as e:
            logger.error(f"Error getting processed feedback entries: {e}")
            return []
    
    async def validate_processing_pipeline(self) -> Dict[str, Any]:
        """
        Validate the processing pipeline by checking stored files.
        
        Returns:
            Dict containing validation results
        """
        try:
            # Get uploaded files
            uploaded_files = await self.cloud_storage.list_feedback_files()
            
            # Get processed files
            processed_files = await self.cloud_storage.list_processed_files()
            
            # Check processing status
            processed_file_ids = set(
                f.get("original_file_id") for f in processed_files 
                if f.get("original_file_id")
            )
            
            pending_processing = []
            for uploaded in uploaded_files:
                if uploaded["file_id"] not in processed_file_ids:
                    pending_processing.append(uploaded)
            
            # Get feedback entries
            feedback_entries = await self.get_processed_feedback_entries()
            
            validation_results = {
                "uploaded_files_count": len(uploaded_files),
                "processed_files_count": len(processed_files),
                "pending_processing_count": len(pending_processing),
                "total_feedback_entries": len(feedback_entries),
                "categories_distribution": {},
                "pending_files": pending_processing,
                "validation_timestamp": datetime.now().isoformat()
            }
            
            # Count categories
            for entry in feedback_entries:
                category = entry.category
                if category not in validation_results["categories_distribution"]:
                    validation_results["categories_distribution"][category] = 0
                validation_results["categories_distribution"][category] += 1
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating processing pipeline: {e}")
            return {
                "error": str(e),
                "validation_timestamp": datetime.now().isoformat()
            }
