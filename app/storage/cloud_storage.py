"""
Google Cloud Storage service for feedback file management.
Handles file uploads, validation, and storage operations for feedback txt files.
"""

import logging
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import mimetypes

try:
    from google.cloud import storage
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    storage = None

logger = logging.getLogger(__name__)

class FeedbackCloudStorage:
    """
    Manages cloud storage operations for feedback files.
    Handles uploads to resources/feedback/ bucket with validation and metadata tracking.
    """
    
    def __init__(self):
        self.bucket_name = "api-project-371618.appspot.com"
        self.feedback_prefix = "resources/feedback/"
        self.processed_prefix = "resources/feedback/processed/"
        
        if not STORAGE_AVAILABLE:
            logger.warning("Google Cloud Storage client not available")
            self.client = None
            self.bucket = None
        else:
            try:
                self.client = storage.Client()
                self.bucket = self.client.bucket(self.bucket_name)
                logger.info(f"Initialized cloud storage client for bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Failed to initialize cloud storage client: {e}")
                self.client = None
                self.bucket = None
    
    def is_available(self) -> bool:
        """Check if cloud storage is available."""
        return self.client is not None and self.bucket is not None
    
    def validate_feedback_file(self, file_content: bytes, filename: str) -> Tuple[bool, str]:
        """
        Validate uploaded feedback file.
        
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
            
            # Check file size (max 10MB)
            if len(file_content) > 10 * 1024 * 1024:
                return False, "File size exceeds 10MB limit"
            
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
            if len(content_str.strip()) < 10:
                return False, "File content is too short (minimum 10 characters)"
            
            # Basic content validation - should contain feedback-like content
            content_lower = content_str.lower()
            feedback_indicators = [
                'feedback', 'improve', 'better', 'suggestion', 'recommend',
                'should', 'could', 'need', 'more', 'less', 'good', 'bad',
                'excellent', 'poor', 'great', 'issue', 'problem', 'fix'
            ]
            
            if not any(indicator in content_lower for indicator in feedback_indicators):
                logger.warning(f"File {filename} may not contain feedback content")
                # Don't reject, just warn
            
            return True, "File is valid"
            
        except Exception as e:
            logger.error(f"Error validating file {filename}: {e}")
            return False, f"Validation error: {str(e)}"
    
    async def upload_feedback_file(self, file_content: bytes, filename: str, 
                                 user_id: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Upload a feedback file to cloud storage.
        
        Args:
            file_content: The file content as bytes
            filename: The original filename
            user_id: ID of the user uploading the file
            metadata: Optional metadata dictionary
            
        Returns:
            Dict containing upload result and file information
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Cloud storage not available",
                "file_id": None
            }
        
        try:
            # Validate file
            is_valid, validation_message = self.validate_feedback_file(file_content, filename)
            if not is_valid:
                return {
                    "success": False,
                    "error": validation_message,
                    "file_id": None
                }
            
            # Generate unique file ID and path
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create safe filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.')).rstrip()
            if not safe_filename:
                safe_filename = "feedback.txt"
            
            # Remove .txt extension for the stored name (we'll add it back)
            base_name = safe_filename.replace('.txt', '')
            stored_filename = f"{timestamp}_{file_id[:8]}_{base_name}.txt"
            blob_path = f"{self.feedback_prefix}{stored_filename}"
            
            # Calculate content hash for deduplication
            content_hash = hashlib.md5(file_content).hexdigest()
            
            # Prepare metadata
            upload_metadata = {
                "file_id": file_id,
                "original_filename": filename,
                "stored_filename": stored_filename,
                "user_id": user_id,
                "upload_timestamp": datetime.now().isoformat(),
                "content_hash": content_hash,
                "file_size": len(file_content),
                "status": "uploaded",
                "processing_status": "pending"
            }
            
            if metadata:
                upload_metadata.update(metadata)
            
            # Upload to cloud storage
            blob = self.bucket.blob(blob_path)
            blob.metadata = upload_metadata
            blob.upload_from_string(file_content, content_type='text/plain')
            
            logger.info(f"Successfully uploaded feedback file: {stored_filename} (ID: {file_id})")
            
            return {
                "success": True,
                "file_id": file_id,
                "stored_filename": stored_filename,
                "blob_path": blob_path,
                "content_hash": content_hash,
                "metadata": upload_metadata
            }
            
        except Exception as e:
            logger.error(f"Error uploading feedback file {filename}: {e}")
            return {
                "success": False,
                "error": f"Upload error: {str(e)}",
                "file_id": None
            }
    
    async def get_feedback_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a feedback file by ID.
        
        Args:
            file_id: The unique file ID
            
        Returns:
            Dict containing file information and content, or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            # List blobs with the file ID in metadata
            blobs = list(self.bucket.list_blobs(prefix=self.feedback_prefix))
            
            for blob in blobs:
                if blob.metadata and blob.metadata.get("file_id") == file_id:
                    content = blob.download_as_text(encoding='utf-8')
                    
                    return {
                        "file_id": file_id,
                        "content": content,
                        "metadata": blob.metadata,
                        "blob_path": blob.name,
                        "size": blob.size,
                        "created": blob.time_created,
                        "updated": blob.updated
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving feedback file {file_id}: {e}")
            return None
    
    async def list_feedback_files(self, user_id: Optional[str] = None, 
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        List feedback files, optionally filtered by user ID.
        
        Args:
            user_id: Optional user ID filter
            limit: Maximum number of files to return
            
        Returns:
            List of file information dictionaries
        """
        if not self.is_available():
            return []
        
        try:
            files = []
            blobs = list(self.bucket.list_blobs(prefix=self.feedback_prefix))
            
            for blob in blobs:
                if blob.metadata:
                    # Skip processed files in this listing
                    if blob.name.startswith(self.processed_prefix):
                        continue
                    
                    # Filter by user ID if specified
                    if user_id and blob.metadata.get("user_id") != user_id:
                        continue
                    
                    files.append({
                        "file_id": blob.metadata.get("file_id"),
                        "original_filename": blob.metadata.get("original_filename"),
                        "stored_filename": blob.metadata.get("stored_filename"),
                        "user_id": blob.metadata.get("user_id"),
                        "upload_timestamp": blob.metadata.get("upload_timestamp"),
                        "file_size": blob.size,
                        "status": blob.metadata.get("status", "unknown"),
                        "processing_status": blob.metadata.get("processing_status", "unknown"),
                        "content_hash": blob.metadata.get("content_hash"),
                        "blob_path": blob.name
                    })
                    
                    if len(files) >= limit:
                        break
            
            # Sort by upload timestamp (most recent first)
            files.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing feedback files: {e}")
            return []
    
    async def delete_feedback_file(self, file_id: str) -> bool:
        """
        Delete a feedback file by ID.
        
        Args:
            file_id: The unique file ID to delete
            
        Returns:
            True if successfully deleted, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Find and delete the blob
            blobs = list(self.bucket.list_blobs(prefix=self.feedback_prefix))
            
            for blob in blobs:
                if blob.metadata and blob.metadata.get("file_id") == file_id:
                    blob.delete()
                    logger.info(f"Deleted feedback file: {file_id}")
                    return True
            
            logger.warning(f"Feedback file not found for deletion: {file_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting feedback file {file_id}: {e}")
            return False
    
    async def store_processed_file(self, file_id: str, processed_content: str, 
                                 tags: List[str], metadata: Dict[str, Any]) -> bool:
        """
        Store a processed feedback file with tags.
        
        Args:
            file_id: Original file ID
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
            
            processed_filename = f"processed_{timestamp}_{file_id[:8]}_{keywords}.json"
            blob_path = f"{self.processed_prefix}{processed_filename}"
            
            # Prepare metadata for processed file
            processed_metadata = {
                "original_file_id": file_id,
                "processed_timestamp": datetime.now().isoformat(),
                "tags": tags,
                "processing_version": "1.0",
                "file_type": "processed_feedback"
            }
            processed_metadata.update(metadata)
            
            # Upload processed file
            blob = self.bucket.blob(blob_path)
            blob.metadata = processed_metadata
            blob.upload_from_string(processed_content, content_type='application/json')
            
            logger.info(f"Stored processed feedback file: {processed_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing processed file for {file_id}: {e}")
            return False
    
    async def list_processed_files(self) -> List[Dict[str, Any]]:
        """
        List all processed feedback files.
        
        Returns:
            List of processed file information
        """
        if not self.is_available():
            return []
        
        try:
            files = []
            blobs = list(self.bucket.list_blobs(prefix=self.processed_prefix))
            
            for blob in blobs:
                if blob.metadata:
                    files.append({
                        "filename": blob.name,
                        "original_file_id": blob.metadata.get("original_file_id"),
                        "processed_timestamp": blob.metadata.get("processed_timestamp"),
                        "tags": blob.metadata.get("tags", []),
                        "file_size": blob.size,
                        "blob_path": blob.name
                    })
            
            # Sort by processed timestamp (most recent first)
            files.sort(key=lambda x: x.get("processed_timestamp", ""), reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing processed files: {e}")
            return []
    
    async def get_processed_file_content(self, filename: str) -> Optional[str]:
        """
        Get the content of a processed feedback file.
        
        Args:
            filename: The processed file name (blob path)
            
        Returns:
            File content as string, or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            blob = self.bucket.blob(filename)
            if blob.exists():
                return blob.download_as_text(encoding='utf-8')
            return None
            
        except Exception as e:
            logger.error(f"Error getting processed file content {filename}: {e}")
            return None


def get_storage_file_content(file_path: str) -> Optional[str]:
    """
    Get the content of a file from cloud storage.

    Args:
        file_path: The full path to the file in the bucket.

    Returns:
        File content as a string, or None if not found.
    """
    if not STORAGE_AVAILABLE:
        logger.warning("Google Cloud Storage client not available")
        return None

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket("api-project-371618.appspot.com")
        blob = bucket.blob(file_path)
        print(f"Attempting to retrieve file from path: {file_path}")

        if blob.exists():
            return blob.download_as_text(encoding='utf-8')
        else:
            logger.error(f"File not found in cloud storage at path: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error getting file from cloud storage {file_path}: {e}")
        return None
