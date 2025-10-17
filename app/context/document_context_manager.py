"""
Document Context Manager for integrating processed reference documents into LLM queries.
Provides intelligent document chunk retrieval and context injection based on query relevance.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..utils.document_processor import DocumentProcessor, DocumentChunk

logger = logging.getLogger(__name__)

class DocumentContextManager:
    """
    Manages document-based context injection for LLM queries.
    Loads processed document chunks and provides relevant context based on query content.
    """
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.document_chunks = []
        self.cache_expiry = timedelta(hours=2)
        self.last_loaded = None
        self._chunks_loaded = False
    
    async def _ensure_chunks_loaded(self) -> bool:
        """
        Ensure document chunks are loaded and up to date.
        
        Returns:
            True if chunks are loaded and current, False otherwise
        """
        now = datetime.now()
        
        # Check if we need to reload chunks
        if (not self._chunks_loaded or 
            self.last_loaded is None or 
            (now - self.last_loaded) > self.cache_expiry):
            
            try:
                logger.info("Loading document chunks for context management")
                self.document_chunks = await self.document_processor.get_processed_document_chunks()
                self.last_loaded = now
                self._chunks_loaded = True
                logger.info(f"Loaded {len(self.document_chunks)} document chunks")
                return True
            except Exception as e:
                logger.error(f"Error loading document chunks: {e}")
                return False
        
        return True
    
    async def get_relevant_document_context(self, 
                                          query: str, 
                                          task_type: str = "general",
                                          max_chunks: int = 5,
                                          max_context_length: int = 4000) -> Dict[str, Any]:
        """
        Get relevant document chunks for a query and format them as context.
        
        Args:
            query: The user query to find relevant context for
            task_type: The type of task being performed
            max_chunks: Maximum number of document chunks to return
            max_context_length: Maximum total length of context content
            
        Returns:
            Dict containing context information and chunks
        """
        try:
            # Ensure chunks are loaded
            if not await self._ensure_chunks_loaded():
                logger.warning("Could not load document chunks")
                return {
                    "has_context": False,
                    "chunks": [],
                    "context_text": "",
                    "source_info": []
                }
            
            if not self.document_chunks:
                logger.info("No document chunks available for context")
                return {
                    "has_context": False,
                    "chunks": [],
                    "context_text": "",
                    "source_info": []
                }
            
            # Search for relevant chunks
            relevant_chunks = self.document_processor.search_relevant_chunks(
                query=query,
                chunks=self.document_chunks,
                max_chunks=max_chunks
            )
            
            if not relevant_chunks:
                logger.info(f"No relevant document chunks found for query: {query[:50]}...")
                return {
                    "has_context": False,
                    "chunks": [],
                    "context_text": "",
                    "source_info": []
                }
            
            # Format context text with length limit
            context_parts = []
            source_info = []
            total_length = 0
            
            for i, chunk in enumerate(relevant_chunks):
                if total_length >= max_context_length:
                    break
                
                # Calculate remaining space
                remaining_length = max_context_length - total_length
                chunk_content = chunk.content
                
                # Truncate if necessary
                if len(chunk_content) > remaining_length:
                    chunk_content = chunk_content[:remaining_length-3] + "..."
                
                # Add chunk info
                source_doc = chunk.metadata.get("source_document", "Unknown")
                chunk_id = chunk.metadata.get("chunk_id", i)
                
                context_parts.append(f"[Document: {source_doc}, Section {chunk_id + 1}]")
                context_parts.append(chunk_content)
                context_parts.append("")  # Empty line for separation
                
                # Track source info
                source_info.append({
                    "document": source_doc,
                    "chunk_id": chunk_id,
                    "relevance_score": chunk.relevance_score,
                    "keywords": chunk.keywords[:5],  # Top 5 keywords
                    "length": len(chunk.content)
                })
                
                total_length += len(chunk_content) + len(f"[Document: {source_doc}, Section {chunk_id + 1}]") + 2
            
            context_text = "\n".join(context_parts)
            
            logger.info(f"Found {len(relevant_chunks)} relevant document chunks for context injection")
            
            return {
                "has_context": True,
                "chunks": relevant_chunks,
                "context_text": context_text,
                "source_info": source_info,
                "total_chunks": len(relevant_chunks),
                "context_length": len(context_text)
            }
            
        except Exception as e:
            logger.error(f"Error getting relevant document context: {e}")
            return {
                "has_context": False,
                "chunks": [],
                "context_text": "",
                "source_info": [],
                "error": str(e)
            }
    
    def inject_document_context(self, 
                              prompt: str, 
                              document_context: Dict[str, Any],
                              task_type: str = "general") -> str:
        """
        Inject document context into a prompt.
        
        Args:
            prompt: The original prompt
            document_context: Context information from get_relevant_document_context
            task_type: The type of task being performed
            
        Returns:
            Enhanced prompt with document context
        """
        if not document_context.get("has_context"):
            return prompt
        
        context_text = document_context.get("context_text", "")
        source_info = document_context.get("source_info", [])
        
        if not context_text:
            return prompt
        
        # Build enhanced prompt
        enhanced_parts = []
        
        # Add context header
        enhanced_parts.append("=" * 80)
        enhanced_parts.append("REFERENCE DOCUMENT CONTEXT")
        enhanced_parts.append("=" * 80)
        enhanced_parts.append("")
        enhanced_parts.append("The following reference documents may contain relevant information for your response:")
        enhanced_parts.append("")
        
        # Add document context
        enhanced_parts.append(context_text)
        
        # Add source summary
        if source_info:
            enhanced_parts.append("=" * 80)
            enhanced_parts.append("CONTEXT SOURCES")
            enhanced_parts.append("=" * 80)
            
            documents_used = set()
            for source in source_info:
                doc_name = source.get("document", "Unknown")
                if doc_name not in documents_used:
                    documents_used.add(doc_name)
                    keywords = ", ".join(source.get("keywords", []))
                    enhanced_parts.append(f"• {doc_name} (Keywords: {keywords})")
            enhanced_parts.append("")
        
        # Add original query
        enhanced_parts.append("=" * 80)
        enhanced_parts.append("USER QUERY")
        enhanced_parts.append("=" * 80)
        enhanced_parts.append(prompt)
        enhanced_parts.append("")
        
        # Add instructions
        enhanced_parts.append("INSTRUCTIONS:")
        enhanced_parts.append("- Use the reference document context above to inform your response")
        enhanced_parts.append("- Cite specific information from the documents when relevant")
        enhanced_parts.append("- If the documents contain conflicting information, note the discrepancies")
        enhanced_parts.append("- If the query cannot be answered using the provided context, state this clearly")
        
        return "\n".join(enhanced_parts)
    
    async def get_document_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded document context.
        
        Returns:
            Dict containing document statistics
        """
        try:
            if not await self._ensure_chunks_loaded():
                return {"error": "Could not load document chunks"}
            
            if not self.document_chunks:
                return {
                    "total_chunks": 0,
                    "total_documents": 0,
                    "avg_chunk_length": 0,
                    "topics_covered": [],
                    "last_updated": self.last_loaded.isoformat() if self.last_loaded else None
                }
            
            # Calculate statistics
            total_chunks = len(self.document_chunks)
            documents = set()
            total_length = 0
            all_keywords = set()
            
            for chunk in self.document_chunks:
                doc_name = chunk.metadata.get("source_document", "Unknown")
                documents.add(doc_name)
                total_length += len(chunk.content)
                all_keywords.update(chunk.keywords)
            
            avg_chunk_length = total_length / total_chunks if total_chunks > 0 else 0
            
            return {
                "total_chunks": total_chunks,
                "total_documents": len(documents),
                "avg_chunk_length": round(avg_chunk_length, 2),
                "total_content_length": total_length,
                "unique_keywords": len(all_keywords),
                "documents_list": sorted(list(documents)),
                "sample_keywords": sorted(list(all_keywords))[:20],  # Top 20 keywords
                "last_updated": self.last_loaded.isoformat() if self.last_loaded else None
            }
            
        except Exception as e:
            logger.error(f"Error getting document statistics: {e}")
            return {"error": str(e)}
    
    async def search_documents(self, 
                             query: str, 
                             limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search documents and return detailed results.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results with detailed information
        """
        try:
            if not await self._ensure_chunks_loaded():
                return []
            
            if not self.document_chunks:
                return []
            
            relevant_chunks = self.document_processor.search_relevant_chunks(
                query=query,
                chunks=self.document_chunks,
                max_chunks=limit
            )
            
            results = []
            for chunk in relevant_chunks:
                results.append({
                    "document": chunk.metadata.get("source_document", "Unknown"),
                    "chunk_id": chunk.metadata.get("chunk_id", 0),
                    "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "full_content": chunk.content,
                    "relevance_score": round(chunk.relevance_score, 3),
                    "keywords": chunk.keywords,
                    "length": len(chunk.content),
                    "timestamp": chunk.timestamp.isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def refresh_document_cache(self) -> bool:
        """
        Force refresh of the document cache.
        
        Returns:
            True if refresh was successful
        """
        try:
            self._chunks_loaded = False
            self.last_loaded = None
            return await self._ensure_chunks_loaded()
        except Exception as e:
            logger.error(f"Error refreshing document cache: {e}")
            return False
