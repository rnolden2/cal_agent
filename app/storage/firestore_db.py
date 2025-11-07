from typing import Union, List, Optional
import logging
import firebase_admin
from firebase_admin import firestore, credentials
import orjson
import asyncio
import re

from ..agent_schema.agent_master_schema import DatabaseModel, UpdateAgentRequest, FeedbackModel, ReportModel, ReportSection

# Initialize Firestore client
# cred = credentials.Certificate("app/config/api-project-37.json")
firebase_admin.initialize_app()
database = "cal-project"
db = firestore.client(database_id=database)

async def store_agent_response(content: str, user_id: str, agent_name: str, topic_id: Optional[str] = None, 
                              llm_provider: Optional[str] = None, llm_model: Optional[str] = None) -> str:
    """Store individual agent response in Firestore database with auto-generated tags and LLM tracking."""
    try:
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        # Validate content before storing
        if not content or content.strip() == "":
            raise ValueError(f"Empty content detected for agent {agent_name}")
        
        # Check for corrupted content patterns
        corrupted_patterns = [
            '{"type":"object","properties":{},"data":{}}',
            '{"type":"object","properties":{}}',
            'type object properties'
        ]
        
        content_lower = content.lower().strip()
        is_corrupted = False
        for pattern in corrupted_patterns:
            if pattern.lower() in content_lower:
                logging.warning(f"Detected potentially corrupted content for agent {agent_name}: {content[:100]}")
                is_corrupted = True
                break
        
        col = db.collection("agent_responses")
        doc_ref = col.document()
        
        # Generate tags from content
        tags = generate_tags_from_content(content, max_tags=20)
        
        # Store the response with agent metadata, tags, and LLM information
        data = {
            "content": content,
            "agent_name": agent_name,
            "user_id": user_id,
            "topic_id": topic_id,
            "tags": tags,
            "response_id": doc_ref.id,
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "content_length": len(content),
            "content_status": "corrupted" if is_corrupted else "valid",
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        
        doc_ref.set(data)
        doc_id = doc_ref.id
        logging.info(f"Agent response stored successfully - ID: {doc_id}, Agent: {agent_name}, LLM: {llm_provider}/{llm_model}, Content length: {len(content)}, Tags: {len(tags)}")
        return doc_id
    except Exception as e:
        logging.error(f"Error writing agent response to Firestore: {e}", exc_info=True)
        # Store error information for debugging
        try:
            error_data = {
                "content": content[:500] if content else "None",  # Store first 500 chars for debugging
                "agent_name": agent_name,
                "user_id": user_id,
                "topic_id": topic_id,
                "llm_provider": llm_provider,
                "llm_model": llm_model,
                "content_status": "error",
                "error_message": str(e),
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            error_col = db.collection("storage_errors")
            error_doc_ref = error_col.document()
            error_doc_ref.set(error_data)
            logging.info(f"Error data stored for debugging with ID: {error_doc_ref.id}")
        except Exception as debug_error:
            logging.error(f"Failed to store error data: {debug_error}")
        
        raise RuntimeError("Failed to write agent response to database") from e


def create_topic_id() -> str:
    """Create a document ID used as a topic_id."""
    try:
        return db.collection("agent_responses").document().id
    except Exception as e:
        logging.error(f"Error creating Firestore document ID: {e}", exc_info=True)
        raise RuntimeError("Failed to create document ID") from e

def set_topic_id(topic_id: Optional[str]) -> str:
    """Sets the topic_id if it's not provided in the request."""
    return topic_id if topic_id else create_topic_id()

def update_agent_document(agent_id: str, update_data: UpdateAgentRequest):
    """Update an existing agent document in Firestore."""
    try:
        agent_ref = db.collection("agents").document(agent_id)
        if not agent_ref.get().exists:
            raise Exception(f"Agent with ID '{agent_id}' does not exist.")
        # Convert Pydantic model to dict, drop None
        update_dict = {
            k: v for k, v in update_data.model_dump().items() if v is not None
        }
        if not update_dict:
            raise Exception("No valid data provided for update.")
        agent_ref.update(update_dict)
        return {"success": f"Agent '{agent_id}' updated successfully."}
    except Exception as e:
        logging.error(f"Error updating Firestore document: {e}", exc_info=True)
        raise RuntimeError("Failed to update Firestore document") from e

async def get_agent_responses(
    topic_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """
    Fetch agent_responses from Firestore, optionally filtered by topic_id and/or user_id.
    Returns up to `limit` items, ordered by timestamp descending.
    """
    def _query():
        # Start with the base collection
        query = db.collection("agent_responses")

        # Apply filters if they are provided
        if topic_id:
            query = query.where(filter=firestore.FieldFilter("topic_id", "==", topic_id))
        if user_id:
            query = query.where(filter=firestore.FieldFilter("user_id", "==", user_id))

        # Order by timestamp descending to get the most recent responses, and limit the result size.
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        return [doc.to_dict() for doc in query.stream()]

    try:
        docs = await asyncio.to_thread(_query)
        responses = []
        for d in docs:
            # Return the full document data including agent_name, tags, and LLM info for UI display
            response_data = {
                "content": d.get("content", ""),
                "agent_name": d.get("agent_name", "Unknown"),
                "topic_id": d.get("topic_id"),
                "user_id": d.get("user_id"),
                "response_id": d.get("response_id"),
                "timestamp": d.get("timestamp"),
                "tags": d.get("tags", []),
                "llm_provider": d.get("llm_provider"),
                "llm_model": d.get("llm_model"),
                "content_length": d.get("content_length"),
                "content_status": d.get("content_status", "unknown")
            }
            responses.append(response_data)
        return responses
    except Exception as e:
        logging.error(f"Error reading from Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to read responses from database") from e

async def get_responses_by_topic_id(topic_id: str) -> List[dict]:
    """
    Fetch all agent responses for a specific topic_id.
    This is useful for getting all agents involved in a single response.
    
    Args:
        topic_id: The topic ID to filter by
        
    Returns:
        List of response documents for the topic
    """
    def _query():
        query = db.collection("agent_responses")
        query = query.where(filter=firestore.FieldFilter("topic_id", "==", topic_id))
        query = query.order_by("timestamp", direction=firestore.Query.ASCENDING)
        return [doc.to_dict() for doc in query.stream()]

    try:
        docs = await asyncio.to_thread(_query)
        responses = []
        for d in docs:
            response_data = {
                "content": d.get("content", ""),
                "agent_name": d.get("agent_name", "Unknown"),
                "topic_id": d.get("topic_id"),
                "user_id": d.get("user_id"),
                "response_id": d.get("response_id"),
                "timestamp": d.get("timestamp"),
                "tags": d.get("tags", [])
            }
            responses.append(response_data)
        
        logging.info(f"Retrieved {len(responses)} agent responses for topic_id: {topic_id}")
        return responses
    except Exception as e:
        logging.error(f"Error reading responses by topic_id from Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to read responses by topic_id from database") from e

async def get_topic_summary(topic_id: str) -> dict:
    """
    Get a summary of all agents and their responses for a specific topic.
    
    Args:
        topic_id: The topic ID to summarize
        
    Returns:
        Dict containing topic summary with agents involved and response count
    """
    try:
        responses = await get_responses_by_topic_id(topic_id)
        
        if not responses:
            return {
                "topic_id": topic_id,
                "agents_involved": [],
                "response_count": 0,
                "user_id": None,
                "timestamp": None
            }
        
        agents_involved = list(set(r["agent_name"] for r in responses))
        user_id = responses[0]["user_id"] if responses else None
        timestamp = responses[0]["timestamp"] if responses else None
        
        return {
            "topic_id": topic_id,
            "agents_involved": agents_involved,
            "response_count": len(responses),
            "user_id": user_id,
            "timestamp": timestamp
        }
    except Exception as e:
        logging.error(f"Error getting topic summary: {e}", exc_info=True)
        raise RuntimeError("Failed to get topic summary") from e

# Read Firestore db Collection "feedback" for feedback entries
async def get_feedback_entries(
    user_id: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """
    Fetch feedback entries from Firestore, optionally filtered by user_id.
    Returns up to `limit` items, ordered by timestamp descending.
    """
    def _query():
        query = db.collection("feedback")
        if user_id:
            query = query.where(filter=firestore.FieldFilter("user_id", "==", user_id))
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        return [doc.to_dict() for doc in query.stream()]

    try:
        docs = await asyncio.to_thread(_query)
        return docs
    except Exception as e:
        logging.error(f"Error reading feedback from Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to read feedback from database") from e  

# Store feedback entry in Firestore db Collection "feedback"
async def store_feedback_entry(feedback: dict) -> str:
    """Store new feedback entry in Firestore database."""
    try:
        col = db.collection("feedback")
        doc_ref = col.document()
        doc_ref.set(feedback)
        doc_id = doc_ref.id
        update_data = {
            "feedback_id": doc_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
        }
        doc_ref.update(update_data)
        logging.info(f"Feedback document created with ID: {doc_id}")
        return doc_id
    except Exception as e:
        logging.error(f"Error writing feedback to Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to write feedback to database") from e

async def delete_agent_response(response_id: str):
    """Delete an agent response document from Firestore."""
    try:
        db.collection("agent_responses").document(response_id).delete()
        logging.info(f"Agent response document deleted: {response_id}")
    except Exception as e:
        logging.error(f"Error deleting agent response document: {e}", exc_info=True)
        raise RuntimeError("Failed to delete agent response document") from e

async def delete_feedback_entry(feedback_id: str):
    """Delete a feedback entry document from Firestore."""
    try:
        db.collection("feedback").document(feedback_id).delete()
        logging.info(f"Feedback entry document deleted: {feedback_id}")
    except Exception as e:
        logging.error(f"Error deleting feedback entry document: {e}", exc_info=True)
        raise RuntimeError("Failed to delete feedback entry document") from e

def clean_json_content(content: str) -> str:
    """
    Clean content by extracting only the JSON portion (from first { to last }).
    This removes any extra text that LLMs sometimes add before or after the JSON.
    
    Args:
        content: The content string to clean
        
    Returns:
        Cleaned content with only the JSON portion, or original if no braces found
    """
    if not content or not isinstance(content, str):
        return content
    
    # Find first { and last }
    first_brace = content.find('{')
    last_brace = content.rfind('}')
    
    # If we found both braces and they're in the right order
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        cleaned = content[first_brace:last_brace + 1]
        
        # Log if we actually cleaned something
        if cleaned != content:
            removed_chars = len(content) - len(cleaned)
            logging.info(f"Cleaned JSON content: removed {removed_chars} extraneous characters")
        
        return cleaned
    
    # Return original if no braces found (might not be JSON)
    return content


def clean_report_content(data: dict) -> dict:
    """
    Recursively clean all 'content' fields in a report data structure.
    This walks through the entire dictionary and cleans any field named 'content'.
    
    Args:
        data: Dictionary that may contain 'content' fields
        
    Returns:
        Dictionary with cleaned content fields
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if key == "content" and isinstance(value, str):
                # Clean this content field
                cleaned[key] = clean_json_content(value)
            elif isinstance(value, (dict, list)):
                # Recursively clean nested structures
                cleaned[key] = clean_report_content(value)
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        # Clean each item in the list
        return [clean_report_content(item) for item in data]
    else:
        return data


def generate_tags_from_content(content: str, max_tags: int = 20) -> List[str]:
    """
    Generate tags from response content by extracting key terms and phrases.
    
    Args:
        content: The response content to analyze
        max_tags: Maximum number of tags to generate (default 20)
        
    Returns:
        List of tags/keywords that summarize the content
    """
    try:
        # Clean and normalize the content
        text = re.sub(r'[^\w\s]', ' ', content.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 'just', 'now', 'here', 'there', 'then', 'type', 
            'object', 'properties', 'type object properties', 'type object', 'object properties'
        }
        
        # Split into words and filter
        words = text.split()
        
        # Extract meaningful words (length > 2, not stop words)
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
                if len(phrase) > 10:  # Only meaningful phrases
                    phrases.append(phrase)
            
            # 2-word phrases
            phrase = ' '.join(meaningful_words[i:i+2])
            if len(phrase) > 6:  # Only meaningful phrases
                phrases.append(phrase)
        
        # Count phrase frequency
        phrase_freq = {}
        for phrase in phrases:
            phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1
        
        # Combine and sort by frequency
        all_tags = []
        
        # Add top single words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        all_tags.extend([word for word, freq in sorted_words[:max_tags//2]])
        
        # Add top phrases
        sorted_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)
        all_tags.extend([phrase for phrase, freq in sorted_phrases[:max_tags//2]])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in all_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)
        
        # Return up to max_tags
        return unique_tags[:max_tags]
        
    except Exception as e:
        logging.error(f"Error generating tags from content: {e}")
        return []

async def search_responses_by_tags(search_terms: List[str], user_id: Optional[str] = None, limit: int = 50) -> List[dict]:
    """
    Search agent responses by tags/keywords.
    
    Args:
        search_terms: List of terms to search for in tags
        user_id: Optional user ID to filter by
        limit: Maximum number of results to return
        
    Returns:
        List of matching response documents with LLM metadata
    """
    def _query():
        query = db.collection("agent_responses")
        
        if user_id:
            query = query.where(filter=firestore.FieldFilter("user_id", "==", user_id))
        
        # For now, we'll get all responses and filter in Python
        # In production, you might want to use Firestore's array-contains-any for better performance
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit * 2)
        return [doc.to_dict() for doc in query.stream()]

    try:
        docs = await asyncio.to_thread(_query)
        matching_responses = []
        
        search_terms_lower = [term.lower() for term in search_terms]
        
        for d in docs:
            tags = d.get("tags", [])
            content = d.get("content", "").lower()
            
            # Check if any search term matches tags or content
            match_found = False
            for term in search_terms_lower:
                if any(term in tag.lower() for tag in tags) or term in content:
                    match_found = True
                    break
            
            if match_found:
                response_data = {
                    "content": d.get("content", ""),
                    "agent_name": d.get("agent_name", "Unknown"),
                    "topic_id": d.get("topic_id"),
                    "user_id": d.get("user_id"),
                    "response_id": d.get("response_id"),
                    "timestamp": d.get("timestamp"),
                    "tags": d.get("tags", []),
                    "llm_provider": d.get("llm_provider"),
                    "llm_model": d.get("llm_model"),
                    "content_length": d.get("content_length"),
                    "content_status": d.get("content_status", "unknown")
                }
                matching_responses.append(response_data)
                
                if len(matching_responses) >= limit:
                    break
        
        logging.info(f"Found {len(matching_responses)} responses matching search terms: {search_terms}")
        return matching_responses
        
    except Exception as e:
        logging.error(f"Error searching responses by tags: {e}", exc_info=True)
        raise RuntimeError("Failed to search responses by tags") from e

def delete_agent_document(agent_id: str):
    """Delete an agent document from Firestore."""
    try:
        db.collection("agents").document(agent_id).delete()
        logging.info(f"Agent document deleted: {agent_id}")
    except Exception as e:
        logging.error(f"Error deleting agent document: {e}", exc_info=True)
        raise RuntimeError("Failed to delete agent document") from e


async def store_feedback(feedback: FeedbackModel) -> str:
    """Store new feedback entry in Firestore database."""
    try:
        col = db.collection("feedback")
        doc_ref = col.document()
        
        # Convert Pydantic model to dict and add metadata
        feedback_data = feedback.model_dump()
        feedback_data.update({
            "feedback_id": doc_ref.id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        
        doc_ref.set(feedback_data)
        doc_id = doc_ref.id
        logging.info(f"Feedback document created with ID: {doc_id}")
        return doc_id
    except Exception as e:
        logging.error(f"Error writing feedback to Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to write feedback to database") from e


async def get_feedback(
    user_id: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """
    Fetch feedback entries from Firestore with optional filtering.
    
    Args:
        user_id: Optional user ID to filter by
        category: Optional category to filter by
        limit: Maximum number of results to return
        
    Returns:
        List of feedback documents
    """
    def _query():
        query = db.collection("feedback")
        
        if user_id:
            query = query.where(filter=firestore.FieldFilter("user_id", "==", user_id))
        if category:
            query = query.where(filter=firestore.FieldFilter("category", "==", category))
            
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        return [doc.to_dict() for doc in query.stream()]

    try:
        docs = await asyncio.to_thread(_query)
        return docs
    except Exception as e:
        logging.error(f"Error reading feedback from Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to read feedback from database") from e


async def store_report(report: ReportModel) -> str:
    """Store new report in Firestore database with cleaned content fields."""
    try:
        col = db.collection("reports")
        doc_ref = col.document()
        
        # Convert Pydantic model to dict and add metadata
        report_data = report.model_dump()
        report_data.update({
            "report_id": doc_ref.id,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        # Clean all content fields before storing
        report_data = clean_report_content(report_data)
        
        doc_ref.set(report_data)
        doc_id = doc_ref.id
        logging.info(f"Report document created with ID: {doc_id} (content fields cleaned)")
        return doc_id
    except Exception as e:
        logging.error(f"Error writing report to Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to write report to database") from e


async def get_report(report_id: str) -> Optional[dict]:
    """Get a specific report by ID."""
    try:
        doc_ref = db.collection("reports").document(report_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        else:
            return None
    except Exception as e:
        logging.error(f"Error reading report from Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to read report from database") from e


async def get_reports(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[dict]:
    """
    Fetch reports from Firestore with optional filtering.
    
    Args:
        user_id: Optional user ID to filter by
        status: Optional status to filter by
        limit: Maximum number of results to return
        
    Returns:
        List of report documents
    """
    def _query():
        query = db.collection("reports")
        
        if user_id:
            query = query.where(filter=firestore.FieldFilter("user_id", "==", user_id))
        if status:
            query = query.where(filter=firestore.FieldFilter("status", "==", status))
            
        query = query.order_by("updated_at", direction=firestore.Query.DESCENDING).limit(limit)
        return [doc.to_dict() for doc in query.stream()]

    try:
        docs = await asyncio.to_thread(_query)
        return docs
    except Exception as e:
        logging.error(f"Error reading reports from Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to read reports from database") from e


async def update_report(report_id: str, updates: dict) -> bool:
    """Update an existing report."""
    try:
        doc_ref = db.collection("reports").document(report_id)
        
        # Add updated timestamp
        updates["updated_at"] = firestore.SERVER_TIMESTAMP
        
        doc_ref.update(updates)
        logging.info(f"Report {report_id} updated successfully")
        return True
    except Exception as e:
        logging.error(f"Error updating report: {e}", exc_info=True)
        raise RuntimeError("Failed to update report") from e


async def update_report_section(report_id: str, section_id: str, content: str, status: str = "completed") -> bool:
    """Update a specific section of a report with cleaned content."""
    try:
        doc_ref = db.collection("reports").document(report_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise RuntimeError(f"Report {report_id} not found")
        
        report_data = doc.to_dict()
        sections = report_data.get("sections", [])
        
        # Clean the content before updating
        cleaned_content = clean_json_content(content)
        
        # Find and update the section
        section_updated = False
        for section in sections:
            if section.get("section_id") == section_id:
                section["content"] = cleaned_content
                section["status"] = status
                section["last_updated"] = firestore.SERVER_TIMESTAMP
                section_updated = True
                break
        
        if not section_updated:
            raise RuntimeError(f"Section {section_id} not found in report {report_id}")
        
        # Update the report
        doc_ref.update({
            "sections": sections,
            "updated_at": firestore.SERVER_TIMESTAMP
        })
        
        logging.info(f"Section {section_id} in report {report_id} updated successfully (content cleaned)")
        return True
    except Exception as e:
        logging.error(f"Error updating report section: {e}", exc_info=True)
        raise RuntimeError("Failed to update report section") from e


async def delete_report(report_id: str) -> bool:
    """Delete a report."""
    try:
        db.collection("reports").document(report_id).delete()
        logging.info(f"Report {report_id} deleted successfully")
        return True
    except Exception as e:
        logging.error(f"Error deleting report: {e}", exc_info=True)
        raise RuntimeError("Failed to delete report") from e
