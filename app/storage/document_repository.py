"""
Document Repository service for knowledge base file management.
Handles uploads, processing, and storage of reference documents for LLM context.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import hashlib

try:
    from google.cloud import storage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    storage = None

logger = logging.getLogger(__name__)

class DocumentRepository:
    """
    Manages cloud storage operations for reference documents and knowledge base files.
    Handles uploads to resources/documents/ bucket with validation and metadata tracking.
    """
    
    def __init__(self):
        self.bucket_name = "api-project-371618.appspot.com"
        self.documents_prefix = "resources/documents/"
        self.processed_prefix = "resources/documents/processed/"
        
        if not STORAGE_AVAILABLE:
            logger.warning("Google Cloud Storage client not available")
            self.client = None
            self.bucket = None
        else:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"Initialized document repository for bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize cloud storage client: {e}")
                self.client = None
                self.bucket = None
    
    def is_available(self) -> bool:
        """Check if cloud storage is available."""
        return self.client is not None and self.bucket is not None
    
    def validate_document_file(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate uploaded document file.
        
        Args:
            file_content: The file content as bytes
            filename: The original filename
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file extension
            if not filename.lower().endswith('.txt'):
                return False, "Only .txt files are allowed"
            
            # Check file size (max 50MB for knowledge documents)
            if len(file_content) > 50 * 1024 * 1024:
                return False, "File size exceeds 50MB limit"
            
            # Check if file is empty
            if len(file_content) == 0:
                return False, "File is empty"
            
            # Try to decode as text
            try:
                content_str = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content_str = file_content.decode('latin-1')
                except UnicodeDecodeError:
                    return False, "File is not valid text (encoding issue)"
            
            # Check if content has meaningful text
            if len(content_str.strip()) < 50:
                return False, "File content is too short (minimum 50 characters for reference documents)"
            
            return True, "Document is valid"
            
        except Exception as e:
            logger.error(f"Error validating document {filename}: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def upload_document(self, file_content: bytes, filename: str, 
                             user_id: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Upload a reference document to cloud storage.
        
        Args:
            file_content: The file content as bytes
            filename: The original filename
            user_id: ID of the user uploading the document
            metadata: Optional metadata dictionary
            
        Returns:
            Dict containing upload result and file information
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Cloud storage not available",
                "document_id": None
            }
        
        try:
            # Validate file
            is_valid, validation_message = self.validate_document_file(file_content, filename)
            if not is_valid:
                return {
                    "success": False,
                    "error": validation_message,
                    "document_id": None
                }
            
            # Generate unique document ID and path
            document_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create safe filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.')).rstrip()
            if not safe_filename:
                safe_filename = "document.txt"
            
            # Remove .txt extension for the stored name (we'll add it back)
            base_name = safe_filename.replace('.txt', '')
            stored_filename = f"{timestamp}_{document_id[:8]}_{base_name}.txt"
            blob_path = f"{self.documents_prefix}{stored_filename}"
            
            # Calculate content hash for deduplication
            content_hash = hashlib.md5(file_content).hexdigest()
            
            # Prepare metadata
            upload_metadata = {
                "document_id": document_id,
                "original_filename": filename,
                "stored_filename": stored_filename,
                "user_id": user_id,
                "upload_timestamp": datetime.now().isoformat(),
                "content_hash": content_hash,
                "file_size": len(file_content),
                "document_type": "reference_document",
                "status": "uploaded",
                "processing_status": "pending"
            }
            
            if metadata:
                upload_metadata.update(metadata)
            
            # Upload to cloud storage
            blob = self.bucket.blob(blob_path)
            blob.metadata = upload_metadata
            blob.upload_from_string(file_content, content_type='text/plain')
            
            logger.info(f"Successfully uploaded document: {stored_filename} (ID: {document_id})")
            
            return {
                "success": True,
                "document_id": document_id,
                "stored_filename": stored_filename,
                "blob_path": blob_path,
                "content_hash": content_hash,
                "metadata": upload_metadata
            }
            
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {e}")
            return {
                "success": False,
                "error": f"Upload error: {str(e)}",
                "document_id": None
            }
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.
        
        Args:
            document_id: The unique document ID
            
        Returns:
            Dict containing document information and content, or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            # List blobs with the document ID in metadata
            blobs = list(self.bucket.list_blobs(prefix=self.documents_prefix))
            
            for blob in blobs:
                if blob.metadata and blob.metadata.get("document_id") == document_id:
                    content = blob.download_as_text(encoding='utf-8')
                    
                    return {
                        "document_id": document_id,
                        "content": content,
                        "metadata": blob.metadata,
                        "blob_path": blob.name,
                        "size": blob.size,
                        "created": blob.time_created,
                        "updated": blob.updated
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            return None
    
    async def list_documents(self, user_id: Optional[str] = None, 
                           limit: int = 50) -> List[Dict[str, Any]]:
        """
        List documents, optionally filtered by user ID.
        
        Args:
            user_id: Optional user ID filter
            limit: Maximum number of documents to return
            
        Returns:
            List of document information dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            documents = []
            blobs = list(self.bucket.list_blobs(prefix=self.documents_prefix))
            
            for blob in blobs:
                if blob.metadata:
                    # Skip processed files in this listing
                    if blob.name.startswith(self.processed_prefix):
                        continue
                    
                    # Filter by user ID if specified
                    if user_id and blob.metadata.get("user_id") != user_id:
                        continue
                    
                    documents.append({
                        "document_id": blob.metadata.get("document_id"),
                        "original_filename": blob.metadata.get("original_filename"),
                        "stored_filename": blob.metadata.get("stored_filename"),
                        "user_id": blob.metadata.get("user_id"),
                        "upload_timestamp": blob.metadata.get("upload_timestamp"),
                        "file_size": blob.size,
                        "status": blob.metadata.get("status", "unknown"),
                        "processing_status": blob.metadata.get("processing_status", "unknown"),
                        "content_hash": blob.metadata.get("content_hash"),
                        "blob_path": blob.name,
                        "document_type": blob.metadata.get("document_type", "reference_document")
                    })
                    
                    if len(documents) >= limit:
                        break
            
            # Sort by upload timestamp (most recent first)
            documents.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: The unique document ID to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Find and delete the blob
            blobs = list(self.bucket.list_blobs(prefix=self.documents_prefix))
            
            for blob in blobs:
                if blob.metadata and blob.metadata.get("document_id") == document_id:
                    blob.delete()
                    logger.info(f"Deleted document: {document_id}")
                    return True
            
            logger.warning(f"Document not found for deletion: {document_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def store_processed_document(self, document_id: str, processed_content: str, 
                                     tags: List[str], metadata: Dict[str, Any]) -> bool:
        """
        Store a processed document with tags and chunks.
        
        Args:
            document_id: Original document ID
            processed_content: Processed content as JSON string
            tags: List of generated tags
            metadata: Processing metadata
            
        Returns:
            True if successfully stored, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            keywords = "_".join(tags[:3])  # Use first 3 tags as keywords
            keywords = "".join(c for c in keywords if c.isalnum() or c == '_')[:30]  # Limit length
            
            processed_filename = f"processed_{timestamp}_{document_id[:8]}_{keywords}.json"
            blob_path = f"{self.processed_prefix}{processed_filename}"
            
            # Prepare metadata for processed document
            processed_metadata = {
                "original_document_id": document_id,
                "processed_timestamp": datetime.now().isoformat(),
                "tags": tags,
                "processing_version": "1.0",
                "file_type": "processed_document"
            }
            processed_metadata.update(metadata)
            
            # Upload processed document
            blob = self.bucket.blob(blob_path)
            blob.metadata = processed_metadata
            blob.upload_from_string(processed_content, content_type='application/json')
            
            logger.info(f"Stored processed document: {processed_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing processed document for {document_id}: {e}")
            return False
    
    async def list_processed_documents(self) -> List[Dict[str, Any]]:
        """
        List all processed documents.
        
        Returns:
            List of processed document information
        """
        if not self.is_available():
            return []
        
        try:
            documents = []
            blobs = list(self.bucket.list_blobs(prefix=self.processed_prefix))
            
            for blob in blobs:
                if blob.metadata:
                    documents.append({
                        "filename": blob.name,
                        "original_document_id": blob.metadata.get("original_document_id"),
                        "processed_timestamp": blob.metadata.get("processed_timestamp"),
                        "tags": blob.metadata.get("tags", []),
                        "file_size": blob.size,
                        "blob_path": blob.name
                    })
            
            # Sort by processed timestamp (most recent first)
            documents.sort(key=lambda x: x.get("processed_timestamp", ""), reverse=True)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing processed documents: {e}")
            return []
    
    async def get_processed_document_content(self, filename: str) -> Optional[str]:
        """
        Get the content of a processed document.
        
        Args:
            filename: The processed document name (blob path)
            
        Returns:
            Document content as string, or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            blob = self.bucket.blob(filename)
            if blob.exists():
                return blob.download_as_text(encoding='utf-8')
            return None
            
        except Exception as e:
            logger.error(f"Error getting processed document content {filename}: {e}")
            return None
