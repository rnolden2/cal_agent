"""
Utility functions for converting various response formats to Markdown
"""

import json
import logging
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)


def convert_to_markdown(content: Any) -> str:
    """
    Convert various content formats to Markdown format.
    
    Args:
        content: Content that could be string, dict, or JSON string
        
    Returns:
        str: Content formatted as Markdown
    """
    try:
        # If content is already a string, check if it's JSON or plain text
        if isinstance(content, str):
            # Try to parse as JSON first
            try:
                json_data = json.loads(content)
                return json_to_markdown(json_data)
            except (json.JSONDecodeError, ValueError):
                # If not JSON, treat as plain text/markdown
                return ensure_markdown_formatting(content)
        
        # If content is a dictionary, convert to markdown
        elif isinstance(content, dict):
            return json_to_markdown(content)
        
        # If content is a list, format as markdown list
        elif isinstance(content, list):
            return list_to_markdown(content)
        
        # For any other type, convert to string
        else:
            return str(content)
            
    except Exception as e:
        logger.error(f"Error converting content to markdown: {e}")
        return str(content)


def json_to_markdown(data: Dict[str, Any]) -> str:
    """
    Convert JSON/dictionary data to well-formatted Markdown.
    
    Args:
        data: Dictionary containing response data
        
    Returns:
        str: Markdown formatted content
    """
    try:
        markdown_parts = []
        
        # Handle specific structured responses like polished_email + summary_of_changes
        if 'polished_email' in data and 'summary_of_changes' in data:
            markdown_parts.append("## Polished Email")
            markdown_parts.append(data['polished_email'])
            markdown_parts.append("\n## Summary of Changes")
            markdown_parts.append(data['summary_of_changes'])
            return '\n\n'.join(markdown_parts)
        
        # Handle common agent response structures
        if 'response' in data:
            response_content = data['response']
            
            # If response is a dict with structured data
            if isinstance(response_content, dict):
                if 'raw_response' in response_content:
                    markdown_parts.append(response_content['raw_response'])
                elif 'content' in response_content:
                    markdown_parts.append(response_content['content'])
                else:
                    # Convert structured response to markdown
                    markdown_parts.append(dict_to_markdown_sections(response_content))
            else:
                # Response is a string
                markdown_parts.append(str(response_content))
        
        # Handle agent metadata
        if 'agent' in data:
            markdown_parts.insert(0, f"**Agent:** {data['agent']}")
        
        # Handle workflow information
        if 'workflow_id' in data:
            markdown_parts.append(f"\n---\n**Workflow ID:** {data['workflow_id']}")
        
        # Handle agents involved
        if 'agents_involved' in data:
            agents = data['agents_involved']
            if isinstance(agents, list):
                markdown_parts.append(f"**Agents Involved:** {', '.join(agents)}")
            else:
                markdown_parts.append(f"**Agents Involved:** {agents}")
        
        # Handle verification results
        if 'verification_results' in data:
            verification = data['verification_results']
            if isinstance(verification, dict):
                markdown_parts.append("\n## Verification Results")
                for key, value in verification.items():
                    formatted_key = key.replace('_', ' ').title()
                    markdown_parts.append(f"- **{formatted_key}:** {value}")
        
        # Handle feedback impact
        if 'feedback_impact' in data:
            feedback = data['feedback_impact']
            if isinstance(feedback, dict):
                markdown_parts.append("\n## Feedback Impact")
                for key, value in feedback.items():
                    formatted_key = key.replace('_', ' ').title()
                    markdown_parts.append(f"- **{formatted_key}:** {value}")
        
        # Handle quality metrics
        if 'quality_score' in data:
            markdown_parts.append(f"**Quality Score:** {data['quality_score']}")
        
        # Handle any remaining fields that might contain useful content
        excluded_fields = {
            'response', 'agent', 'workflow_id', 'agents_involved', 
            'verification_results', 'feedback_impact', 'quality_score',
            'timestamp', 'user_id', 'topic_id', 'response_id',
            'polished_email', 'summary_of_changes'  # Already handled above
        }
        
        for key, value in data.items():
            if key not in excluded_fields and value:
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, (dict, list)):
                    markdown_parts.append(f"\n## {formatted_key}")
                    markdown_parts.append(convert_to_markdown(value))
                else:
                    markdown_parts.append(f"**{formatted_key}:** {value}")
        
        return '\n\n'.join(filter(None, markdown_parts))
        
    except Exception as e:
        logger.error(f"Error converting JSON to markdown: {e}")
        return str(data)


def dict_to_markdown_sections(data: Dict[str, Any]) -> str:
    """
    Convert a dictionary to markdown sections.
    
    Args:
        data: Dictionary to convert
        
    Returns:
        str: Markdown formatted sections
    """
    sections = []
    
    for key, value in data.items():
        formatted_key = key.replace('_', ' ').title()
        
        if isinstance(value, dict):
            sections.append(f"## {formatted_key}")
            sections.append(dict_to_markdown_sections(value))
        elif isinstance(value, list):
            sections.append(f"## {formatted_key}")
            sections.append(list_to_markdown(value))
        else:
            sections.append(f"**{formatted_key}:** {value}")
    
    return '\n\n'.join(sections)


def list_to_markdown(items: list) -> str:
    """
    Convert a list to markdown format.
    
    Args:
        items: List to convert
        
    Returns:
        str: Markdown formatted list
    """
    if not items:
        return ""
    
    markdown_items = []
    
    for item in items:
        if isinstance(item, dict):
            # For dict items, create a sub-section
            markdown_items.append(f"- {dict_to_markdown_sections(item)}")
        elif isinstance(item, list):
            # For nested lists, indent
            nested = list_to_markdown(item)
            indented = '\n'.join(f"  {line}" for line in nested.split('\n'))
            markdown_items.append(f"- {indented}")
        else:
            markdown_items.append(f"- {item}")
    
    return '\n'.join(markdown_items)


def ensure_markdown_formatting(text: str) -> str:
    """
    Ensure text has proper markdown formatting.
    
    Args:
        text: Plain text that might need markdown formatting
        
    Returns:
        str: Text with improved markdown formatting
    """
    if not text:
        return ""
    
    # If text already looks like markdown, return as-is
    markdown_indicators = ['#', '*', '-', '`', '>', '|', '[', ']']
    if any(indicator in text for indicator in markdown_indicators):
        return text
    
    # For plain text, add basic formatting
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            formatted_lines.append('')
            continue
        
        # Check if line looks like a title (short, no punctuation at end)
        if len(line) < 60 and not line.endswith(('.', '!', '?', ':')):
            # Check if next lines are longer (indicating this might be a title)
            formatted_lines.append(f"## {line}")
        else:
            formatted_lines.append(line)
    
    return '\n\n'.join(formatted_lines)


def format_agent_response_for_display(response_data: Dict[str, Any]) -> str:
    """
    Format agent response data specifically for frontend display.
    
    Args:
        response_data: Response data from database
        
    Returns:
        str: Markdown formatted content ready for display
    """
    try:
        content = response_data.get('content', '')
        agent_name = response_data.get('agent_name', 'Unknown')
        
        # Convert content to markdown
        markdown_content = convert_to_markdown(content)
        
        # Add agent header if not already present
        if not markdown_content.startswith(f"**Agent:** {agent_name}"):
            markdown_content = f"**Agent:** {agent_name}\n\n{markdown_content}"
        
        # Add metadata footer if available
        metadata_parts = []
        
        if response_data.get('topic_id'):
            metadata_parts.append(f"**Topic ID:** {response_data['topic_id']}")
        
        if response_data.get('tags'):
            tags = response_data['tags']
            if isinstance(tags, list) and tags:
                metadata_parts.append(f"**Tags:** {', '.join(tags)}")
        
        if response_data.get('timestamp'):
            metadata_parts.append(f"**Timestamp:** {response_data['timestamp']}")
        
        if metadata_parts:
            markdown_content += f"\n\n---\n\n{chr(10).join(metadata_parts)}"
        
        return markdown_content
        
    except Exception as e:
        logger.error(f"Error formatting agent response for display: {e}")
        return str(response_data.get('content', 'Error formatting response'))
