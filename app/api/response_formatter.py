"""
API endpoint for formatting agent responses to Markdown
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import logging

from ..storage.firestore_db import get_agent_responses, get_responses_by_topic_id
from ..utils.markdown_converter import format_agent_response_for_display, convert_to_markdown

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/responses/formatted")
async def get_formatted_responses(
    topic_id: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Get agent responses with content formatted as Markdown.
    
    Args:
        topic_id: Optional topic ID to filter by
        user_id: Optional user ID to filter by
        limit: Maximum number of responses to return
        
    Returns:
        List of responses with markdown-formatted content
    """
    try:
        # Get raw responses from database
        responses = await get_agent_responses(topic_id=topic_id, user_id=user_id, limit=limit)
        
        # Format each response for display
        formatted_responses = []
        for response in responses:
            try:
                # Create a copy of the response
                formatted_response = response.copy()
                
                # Format the content as markdown
                formatted_content = format_agent_response_for_display(response)
                formatted_response['formatted_content'] = formatted_content
                
                # Keep original content for reference
                formatted_response['original_content'] = response.get('content', '')
                
                formatted_responses.append(formatted_response)
                
            except Exception as e:
                logger.error(f"Error formatting individual response: {e}")
                # Include the response with error info
                error_response = response.copy()
                error_response['formatted_content'] = f"Error formatting response: {str(e)}"
                error_response['original_content'] = response.get('content', '')
                formatted_responses.append(error_response)
        
        logger.info(f"Successfully formatted {len(formatted_responses)} responses")
        return formatted_responses
        
    except Exception as e:
        logger.error(f"Error getting formatted responses: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving formatted responses: {str(e)}")


@router.get("/responses/topic/{topic_id}/formatted")
async def get_formatted_responses_by_topic(topic_id: str) -> List[Dict[str, Any]]:
    """
    Get all formatted agent responses for a specific topic ID.
    
    Args:
        topic_id: The topic ID to filter by
        
    Returns:
        List of formatted responses for the topic
    """
    try:
        # Get raw responses from database
        responses = await get_responses_by_topic_id(topic_id)
        
        # Format each response for display
        formatted_responses = []
        for response in responses:
            try:
                # Create a copy of the response
                formatted_response = response.copy()
                
                # Format the content as markdown
                formatted_content = format_agent_response_for_display(response)
                formatted_response['formatted_content'] = formatted_content
                
                # Keep original content for reference
                formatted_response['original_content'] = response.get('content', '')
                
                formatted_responses.append(formatted_response)
                
            except Exception as e:
                logger.error(f"Error formatting individual response: {e}")
                # Include the response with error info
                error_response = response.copy()
                error_response['formatted_content'] = f"Error formatting response: {str(e)}"
                error_response['original_content'] = response.get('content', '')
                formatted_responses.append(error_response)
        
        logger.info(f"Successfully formatted {len(formatted_responses)} responses for topic {topic_id}")
        return formatted_responses
        
    except Exception as e:
        logger.error(f"Error getting formatted responses for topic {topic_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving formatted responses for topic: {str(e)}")


@router.post("/responses/format")
async def format_content(content: Dict[str, Any]) -> Dict[str, str]:
    """
    Format arbitrary content as Markdown.
    
    Args:
        content: Content to format (can be string, dict, or complex structure)
        
    Returns:
        Dict containing original and formatted content
    """
    try:
        original_content = content.get('content', content)
        formatted_content = convert_to_markdown(original_content)
        
        return {
            'original_content': str(original_content),
            'formatted_content': formatted_content,
            'format_type': 'markdown'
        }
        
    except Exception as e:
        logger.error(f"Error formatting content: {e}")
        raise HTTPException(status_code=500, detail=f"Error formatting content: {str(e)}")
