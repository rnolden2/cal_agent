"""
Document processor for reference documents and knowledge base files.
Converts plain text documents into chunked, indexed content for LLM context injection.
"""

import logging
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import asyncio

from ..storage.document_repository import DocumentRepository

logger = logging.getLogger(__name__)

class DocumentChunk:
    """Represents a chunk of processed document content."""
    
    def __init__(self, content: str, chunk_id: int, metadata: Dict[str, Any]):
        self.content = content
        self.chunk_id = chunk_id
        self.metadata = metadata
        self.keywords = []
        self.relevance_score = 0.0
        self.timestamp = datetime.now()

class DocumentProcessor:
    """
    Processes uploaded reference documents into chunked, searchable content.
    Handles text chunking, topic extraction, and indexing for efficient LLM integration.
    """
    
    def __init__(self):
        self.document_repository = DocumentRepository()
        
        # Common stop words for better keyword extraction
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
    
    def _chunk_text(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation.
        
        Args:
            text: The text to chunk
            chunk_size: Target size for each chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundaries
            if end < len(text):
                # Look for sentence ending within the last 200 characters
                sentence_end = text.rfind('.', end - 200, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for paragraph break
                    para_break = text.rfind('\n\n', end - 200, end)
                    if para_break > start + chunk_size // 2:
                        end = para_break + 2
                    else:
                        # Look for any line break
                        line_break = text.rfind('\n', end - 100, end)
                        if line_break > start + chunk_size // 2:
                            end = line_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calculate next start position with overlap
            if end >= len(text):
                break
            start = max(start + 1, end - overlap)
        
        return chunks
    
    def _extract_keywords(self, text: str, max_keywords: int = 15) -> List[str]:
        """
        Extract keywords and key phrases from document text.
        
        Args:
            text: The text to analyze
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of keywords and phrases
        """
        # Clean and normalize text
        text_clean = re.sub(r'[^\w\s]', ' ', text.lower())
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()
        
        # Split into words and filter
        words = text_clean.split()
        meaningful_words = [
            word for word in words 
            if len(word) > 3 and word not in self.stop_words and word.isalpha()
        ]
        
        # Count word frequency
        word_freq = {}
        for word in meaningful_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Extract multi-word phrases (2-4 words)
        phrases = []
        for i in range(len(meaningful_words) - 1):
            # 2-word phrases
            if i < len(meaningful_words) - 1:
                phrase = ' '.join(meaningful_words[i:i+2])
                if len(phrase) > 8:
                    phrases.append(phrase)
            
            # 3-word phrases
            if i < len(meaningful_words) - 2:
                phrase = ' '.join(meaningful_words[i:i+3])
                if len(phrase) > 12:
                    phrases.append(phrase)
            
            # 4-word phrases for very specific concepts
            if i < len(meaningful_words) - 3:
                phrase = ' '.join(meaningful_words[i:i+4])
                if len(phrase) > 16:
                    phrases.append(phrase)
        
        # Count phrase frequency
        phrase_freq = {}
        for phrase in phrases:
            phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1
        
        # Combine and prioritize
        all_keywords = []
        
        # Add top single words (weighted by frequency)
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        for word, freq in sorted_words[:max_keywords//2]:
            if freq > 1:  # Only include words that appear multiple times
                all_keywords.append(word)
        
        # Add top phrases (weighted by frequency and length)
        sorted_phrases = sorted(phrase_freq.items(), key=lambda x: (x[1], len(x[0])), reverse=True)
        for phrase, freq in sorted_phrases[:max_keywords//2]:
            if freq > 1 or len(phrase) > 20:  # Include high-frequency or very specific phrases
                all_keywords.append(phrase)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in all_keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:max_keywords]
    
    def _identify_document_topics(self, text: str) -> List[str]:
        """
        Identify main topics/themes in the document.
        
        Args:
            text: The document text to analyze
            
        Returns:
            List of identified topics
        """
        text_lower = text.lower()
        topics = []
        
        # Technical topics
        tech_indicators = {
            'technical_documentation': ['api', 'documentation', 'technical', 'specification', 'protocol', 'implementation'],
            'software_development': ['code', 'programming', 'development', 'software', 'framework', 'library'],
            'system_architecture': ['architecture', 'system', 'design', 'infrastructure', 'deployment'],
            'data_analysis': ['data', 'analysis', 'analytics', 'statistics', 'metrics', 'reporting'],
            'security': ['security', 'authentication', 'authorization', 'encryption', 'privacy'],
            'networking': ['network', 'protocol', 'connection', 'server', 'client', 'endpoint']
        }
        
        # Business topics
        business_indicators = {
            'business_strategy': ['strategy', 'business', 'market', 'competitive', 'growth', 'revenue'],
            'project_management': ['project', 'management', 'planning', 'timeline', 'milestone', 'deliverable'],
            'customer_relations': ['customer', 'client', 'user', 'feedback', 'support', 'service'],
            'financial': ['financial', 'budget', 'cost', 'pricing', 'investment', 'roi'],
            'marketing': ['marketing', 'promotion', 'branding', 'campaign', 'advertising'],
            'operations': ['operations', 'process', 'workflow', 'procedure', 'standard', 'policy']
        }
        
        # Industry topics
        industry_indicators = {
            'healthcare': ['healthcare', 'medical', 'patient', 'clinical', 'hospital', 'treatment'],
            'finance': ['finance', 'banking', 'investment', 'trading', 'financial', 'economic'],
            'education': ['education', 'learning', 'student', 'academic', 'curriculum', 'training'],
            'manufacturing': ['manufacturing', 'production', 'factory', 'assembly', 'quality', 'industrial'],
            'retail': ['retail', 'sales', 'commerce', 'store', 'inventory', 'merchandise'],
            'legal': ['legal', 'law', 'compliance', 'regulation', 'contract', 'agreement']
        }
        
        all_indicators = {**tech_indicators, **business_indicators, **industry_indicators}
        
        for topic, indicators in all_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            if score >= 2:  # Require at least 2 indicators for topic identification
                topics.append(topic)
        
        # Add generic topic if no specific topics found
        if not topics:
            topics.append('general_reference')
        
        return topics
    
    async def process_document(self, document_id: str) -> Dict[str, Any]:
        """
        Process an uploaded document into chunked, indexed content.
        
        Args:
            document_id: The ID of the uploaded document to process
            
        Returns:
            Dict containing processing results
        """
        try:
            # Get the document from repository
            document_info = await self.document_repository.get_document(document_id)
            if not document_info:
                return {
                    "success": False,
                    "error": f"Document {document_id} not found",
                    "document_id": document_id
                }
            
            content = document_info["content"]
            metadata = document_info["metadata"]
            
            logger.info(f"Processing document: {document_id}")
            
            # Extract overall document information
            document_keywords = self._extract_keywords(content, max_keywords=20)
            document_topics = self._identify_document_topics(content)
            
            # Chunk the document
            text_chunks = self._chunk_text(content)
            
            # Process each chunk
            processed_chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunk_keywords = self._extract_keywords(chunk_text, max_keywords=8)
                chunk_metadata = {
                    "chunk_id": i,
                    "total_chunks": len(text_chunks),
                    "char_start": content.find(chunk_text[:50]) if len(chunk_text) > 50 else content.find(chunk_text),
                    "char_length": len(chunk_text),
                    "keywords": chunk_keywords,
                    "source_document": metadata.get("original_filename", "unknown")
                }
                
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_id=i,
                    metadata=chunk_metadata
                )
                chunk.keywords = chunk_keywords
                processed_chunks.append(chunk)
            
            # Create processed document structure
            processed_content = {
                "document_id": document_id,
                "original_filename": metadata.get("original_filename"),
                "processed_timestamp": datetime.now().isoformat(),
                "processing_version": "1.0",
                "total_chunks": len(processed_chunks),
                "document_topics": document_topics,
                "document_keywords": document_keywords,
                "chunks": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "keywords": chunk.keywords,
                        "metadata": chunk.metadata,
                        "char_length": len(chunk.content),
                        "timestamp": chunk.timestamp.isoformat()
                    }
                    for chunk in processed_chunks
                ],
                "statistics": {
                    "total_length": len(content),
                    "chunks_count": len(processed_chunks),
                    "avg_chunk_length": sum(len(c.content) for c in processed_chunks) / len(processed_chunks),
                    "topics_identified": document_topics,
                    "unique_keywords": len(set(document_keywords)),
                    "processing_date": datetime.now().isoformat()
                }
            }
            
            # Generate tags for storage
            file_tags = document_topics[:3] + document_keywords[:7]  # Use topics and top keywords as tags
            
            # Store processed document
            processed_json = json.dumps(processed_content, indent=2)
            processing_metadata = {
                "original_user_id": metadata.get("user_id"),
                "chunks_count": len(processed_chunks),
                "document_topics": document_topics,
                "total_length": len(content),
                "keywords_count": len(document_keywords)
            }
            
            success = await self.document_repository.store_processed_document(
                document_id=document_id,
                processed_content=processed_json,
                tags=file_tags,
                metadata=processing_metadata
            )
            
            if success:
                logger.info(f"Successfully processed document: {document_id} ({len(processed_chunks)} chunks)")
                return {
                    "success": True,
                    "document_id": document_id,
                    "chunks_count": len(processed_chunks),
                    "document_topics": document_topics,
                    "file_tags": file_tags,
                    "processed_content": processed_content
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to store processed document",
                    "document_id": document_id
                }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            return {
                "success": False,
                "error": f"Processing error: {str(e)}",
                "document_id": document_id
            }
    
    async def batch_process_documents(self, document_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch.
        
        Args:
            document_ids: List of document IDs to process
            
        Returns:
            List of processing results
        """
        results = []
        
        for document_id in document_ids:
            try:
                result = await self.process_document(document_id)
                results.append(result)
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in batch processing document {document_id}: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "document_id": document_id
                })
        
        return results
    
    async def get_processed_document_chunks(self) -> List[DocumentChunk]:
        """
        Load all processed documents and return as searchable chunks.
        
        Returns:
            List of DocumentChunk objects from all processed documents
        """
        try:
            processed_documents = await self.document_repository.list_processed_documents()
            all_chunks = []
            
            for doc_info in processed_documents:
                try:
                    content_json = await self.document_repository.get_processed_document_content(
                        doc_info["filename"]
                    )
                    
                    if content_json:
                        content_data = json.loads(content_json)
                        
                        # Convert stored chunks back to DocumentChunk objects
                        for chunk_data in content_data.get("chunks", []):
                            chunk = DocumentChunk(
                                content=chunk_data["content"],
                                chunk_id=chunk_data["chunk_id"],
                                metadata=chunk_data["metadata"]
                            )
                            chunk.keywords = chunk_data.get("keywords", [])
                            chunk.timestamp = datetime.fromisoformat(chunk_data["timestamp"])
                            all_chunks.append(chunk)
                
                except Exception as e:
                    logger.error(f"Error loading processed document {doc_info['filename']}: {e}")
                    continue
            
            logger.info(f"Loaded {len(all_chunks)} document chunks from {len(processed_documents)} processed documents")
            return all_chunks
            
        except Exception as e:
            logger.error(f"Error getting processed document chunks: {e}")
            return []
    
    def search_relevant_chunks(self, query: str, chunks: List[DocumentChunk], 
                             max_chunks: int = 5) -> List[DocumentChunk]:
        """
        Search for document chunks relevant to a query.
        
        Args:
            query: The search query
            chunks: List of available document chunks
            max_chunks: Maximum number of chunks to return
            
        Returns:
            List of relevant DocumentChunk objects
        """
        if not chunks:
            return []
        
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        # Score chunks based on relevance
        scored_chunks = []
        for chunk in chunks:
            score = 0.0
            chunk_content_lower = chunk.content.lower()
            
            # Exact phrase matches (high weight)
            if query_lower in chunk_content_lower:
                score += 5.0
            
            # Keyword matches in chunk keywords (medium weight)
            chunk_keywords_lower = [kw.lower() for kw in chunk.keywords]
            for query_word in query_words:
                if any(query_word in kw for kw in chunk_keywords_lower):
                    score += 2.0
            
            # Word matches in content (low weight)
            chunk_words = set(re.findall(r'\w+', chunk_content_lower))
            word_overlap = len(query_words.intersection(chunk_words))
            score += word_overlap * 0.5
            
            # Boost score for recent chunks
            days_old = (datetime.now() - chunk.timestamp).days
            if days_old < 30:
                score += 0.5
            
            chunk.relevance_score = score
            if score > 0:
                scored_chunks.append(chunk)
        
        # Sort by relevance and return top chunks
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_chunks[:max_chunks]
    
    async def validate_document_processing_pipeline(self) -> Dict[str, Any]:
        """
        Validate the document processing pipeline by checking stored files.
        
        Returns:
            Dict containing validation results
        """
        try:
            # Get uploaded documents
            uploaded_documents = await self.document_repository.list_documents()
            
            # Get processed documents
            processed_documents = await self.document_repository.list_processed_documents()
            
            # Check processing status
            processed_document_ids = set(
                d.get("original_document_id") for d in processed_documents 
                if d.get("original_document_id")
            )
            
            pending_processing = []
            for uploaded in uploaded_documents:
                if uploaded["document_id"] not in processed_document_ids:
                    pending_processing.append(uploaded)
            
            # Get document chunks
            document_chunks = await self.get_processed_document_chunks()
            
            # Count topics
            topic_distribution = {}
            for doc in processed_documents:
                if doc.get("tags"):
                    for tag in doc["tags"]:
                        if tag not in topic_distribution:
                            topic_distribution[tag] = 0
                        topic_distribution[tag] += 1
            
            validation_results = {
                "uploaded_documents_count": len(uploaded_documents),
                "processed_documents_count": len(processed_documents),
                "pending_processing_count": len(pending_processing),
                "total_document_chunks": len(document_chunks),
                "topic_distribution": topic_distribution,
                "pending_documents": pending_processing,
                "validation_timestamp": datetime.now().isoformat()
            }
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating document processing pipeline: {e}")
            return {
                "error": str(e),
                "validation_timestamp": datetime.now().isoformat()
            }
