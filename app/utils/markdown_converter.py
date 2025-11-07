"""
Utility functions for converting various response formats to Markdown
"""

import json
import logging
import re
from typing import Any, Dict, Union, List

logger = logging.getLogger(__name__)


def preprocess_mixed_content(content: str) -> str:
    """
    Preprocess mixed content containing multiple JSON objects with markdown titles and bytecode.
    
    Args:
        content: String containing mixed JSON objects, markdown titles, and possibly bytecode
        
    Returns:
        str: Clean markdown formatted content
    """
    try:
        # Step 1: Check if content is bytecode and decode it
        if content.startswith("b'") or content.startswith('b"'):
            try:
                # Remove the b' prefix and trailing quote, then decode
                content = content[2:-1]
                # Handle escaped characters
                content = content.encode('utf-8').decode('unicode_escape')
            except Exception as e:
                logger.warning(f"Failed to decode bytecode: {e}")
        
        # Step 2: Remove markdown titles (lines starting with ##)
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith('##'):
                cleaned_lines.append(line)
        content = '\n'.join(cleaned_lines)
        
        # Step 3: Extract individual JSON objects using a more robust method
        # Split by newlines and look for JSON object boundaries
        json_objects = []
        current_json = ""
        brace_count = 0
        in_string = False
        escape_next = False
        
        for char in content:
            if escape_next:
                current_json += char
                escape_next = False
                continue
            
            if char == '\\':
                current_json += char
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
            
            if not in_string:
                if char == '{':
                    if brace_count == 0:
                        current_json = ""
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        current_json += char
                        json_objects.append(current_json.strip())
                        current_json = ""
                        continue
            
            if brace_count > 0:
                current_json += char
        
        if not json_objects:
            # No JSON found, return as plain text
            return ensure_markdown_formatting(content)
        
        # Step 4: Process each JSON object
        markdown_parts = []
        for i, json_str in enumerate(json_objects):
            try:
                # Parse the JSON
                json_data = json.loads(json_str)
                
                # Convert to markdown
                md_content = json_to_markdown(json_data)
                
                # Add separator between multiple responses
                if i > 0:
                    markdown_parts.append('\n\n---\n\n')
                
                markdown_parts.append(md_content)
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON object {i+1}: {e}")
                # Include as plain text with clear labeling
                if i > 0:
                    markdown_parts.append('\n\n---\n\n')
                markdown_parts.append(f"**Failed to parse JSON block {i+1}**\n\n```\n{json_str[:500]}...\n```")
            except Exception as e:
                logger.error(f"Error processing JSON object {i+1}: {e}")
                if i > 0:
                    markdown_parts.append('\n\n---\n\n')
                markdown_parts.append(f"**Error processing block {i+1}**: {str(e)}")
        
        return '\n\n'.join(markdown_parts)
        
    except Exception as e:
        logger.error(f"Error in preprocess_mixed_content: {e}")
        return ensure_markdown_formatting(content)


def convert_to_markdown(content: Any) -> str:
    """
    Convert various content formats to Markdown format.
    
    Args:
        content: Content that could be string, dict, or JSON string
        
    Returns:
        str: Content formatted as Markdown
    """
    try:
        # If content is already a string, check if it needs preprocessing
        if isinstance(content, str):
            # Check if content contains multiple JSONs with markdown titles or bytecode
            has_markdown_titles = '##' in content and '\n' in content
            has_multiple_jsons = content.count('{') > 1
            is_bytecode = content.startswith("b'") or content.startswith('b"')
            
            # If it's mixed content, preprocess it
            if (has_markdown_titles and has_multiple_jsons) or is_bytecode:
                return preprocess_mixed_content(content)
            
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


def json_to_markdown(data: Dict[str, Any], level: int = 0) -> str:
    """
    Convert JSON/dictionary data to well-formatted Markdown.
    
    Args:
        data: Dictionary containing response data
        level: Indentation level for nested structures
        
    Returns:
        str: Markdown formatted content
    """
    try:
        markdown_parts = []
        
        # Check for report schema structure
        if all(key in data for key in ['title', 'executiveSummary', 'sections']):
            # Format as report
            markdown_parts.append(f"# {data.get('title', 'Untitled Report')}")
            
            markdown_parts.append("## Executive Summary")
            markdown_parts.append(data.get('executiveSummary', ''))
            
            for section in data.get('sections', []):
                markdown_parts.append(f"## {section.get('sectionTitle', 'Untitled Section')}")
                markdown_parts.append(section.get('content', ''))
                
                for sub in section.get('subsections', []):
                    markdown_parts.append(f"### {sub.get('subsectionTitle', 'Untitled Subsection')}")
                    markdown_parts.append(sub.get('content', ''))
            
            if data.get('recommendations'):
                markdown_parts.append("## Recommendations")
                for rec in data['recommendations']:
                    markdown_parts.append(f"- **{rec.get('title', '')}:** {rec.get('details', '')}")
            
            if data.get('conclusion'):
                markdown_parts.append("## Conclusion")
                markdown_parts.append(data['conclusion'])
            
            if data.get('metadata'):
                markdown_parts.append("## Metadata")
                if data['metadata'].get('sources'):
                    markdown_parts.append("**Sources:**")
                    for source in data['metadata']['sources']:
                        markdown_parts.append(f"- {source}")
                if data['metadata'].get('date'):
                    markdown_parts.append(f"**Date:** {data['metadata']['date']}")
            
            return '\n\n'.join(filter(None, markdown_parts))
        
        # Handle specific structured responses like polished_email + summary_of_changes
        if 'polished_email' in data and 'summary_of_changes' in data:
            markdown_parts.append("## Polished Email")
            markdown_parts.append(data['polished_email'])
            markdown_parts.append("\n## Summary of Changes")
            markdown_parts.append(data['summary_of_changes'])
            return '\n\n'.join(markdown_parts)
        
        # Handle content field with nested structures
        if 'content' in data and isinstance(data['content'], dict):
            for key, value in data['content'].items():
                if isinstance(value, dict):
                    # Format as section header
                    markdown_parts.append(f"## {key}")
                    
                    # Handle Purpose field specially
                    if 'Purpose' in value:
                        markdown_parts.append(f"**Purpose:** {value['Purpose']}\n")
                    
                    # Handle Table field - convert to markdown table
                    if 'Table' in value and isinstance(value['Table'], list):
                        table_md = dict_list_to_md_table(value['Table'])
                        markdown_parts.append(table_md)
                    
                    # Handle Updates field - convert to list or table
                    if 'Updates' in value and isinstance(value['Updates'], list):
                        updates_md = dict_list_to_md_table(value['Updates'])
                        markdown_parts.append(updates_md)
                    
                    # Handle any other nested dicts
                    for sub_key, sub_value in value.items():
                        if sub_key not in ['Purpose', 'Table', 'Updates']:
                            if isinstance(sub_value, (dict, list)):
                                markdown_parts.append(f"\n### {sub_key}")
                                markdown_parts.append(convert_to_markdown(sub_value))
                            elif sub_value:
                                markdown_parts.append(f"**{sub_key}:** {sub_value}")
        
        # Handle common agent response structures with 'response' field
        if 'response' in data:
            response_content = data['response']
            
            # If response is a dict with structured data
            if isinstance(response_content, dict):
                if 'raw_response' in response_content:
                    markdown_parts.append(response_content['raw_response'])
                elif 'content' in response_content:
                    # Check if content is a string containing markdown or needs parsing
                    content_val = response_content['content']
                    if isinstance(content_val, str):
                        # Check if it's pre-formatted markdown or needs processing
                        if content_val.strip().startswith('#') or '|' in content_val:
                            markdown_parts.append(content_val)
                        else:
                            markdown_parts.append(ensure_markdown_formatting(content_val))
                    else:
                        markdown_parts.append(convert_to_markdown(content_val))
                else:
                    # Convert structured response to markdown
                    markdown_parts.append(dict_to_markdown_sections(response_content, level))
            else:
                # Response is a string
                markdown_parts.append(str(response_content))
        
        # Handle context field
        if 'context' in data and not 'content' in data:
            context = data['context']
            if isinstance(context, str) and len(context) > 100:
                markdown_parts.append("### Context")
                markdown_parts.append(context[:500] + "..." if len(context) > 500 else context)
        
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
            'polished_email', 'summary_of_changes',  # Already handled above
            'content', 'context', 'type', 'properties', 'data'  # Handled specially
        }
        
        for key, value in data.items():
            if key not in excluded_fields and value:
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, (dict, list)):
                    markdown_parts.append(f"\n## {formatted_key}")
                    markdown_parts.append(convert_to_markdown(value))
                elif value and str(value).strip():
                    markdown_parts.append(f"**{formatted_key}:** {value}")
        
        return '\n\n'.join(filter(None, markdown_parts))
        
    except Exception as e:
        logger.error(f"Error converting JSON to markdown: {e}")
        return str(data)


def dict_to_markdown_sections(data: Dict[str, Any], level: int = 0) -> str:
    """
    Convert a dictionary to markdown sections.
    
    Args:
        data: Dictionary to convert
        level: Nesting level for headers
        
    Returns:
        str: Markdown formatted sections
    """
    sections = []
    header_prefix = "#" * min(level + 2, 6)  # Limit to h6
    
    for key, value in data.items():
        formatted_key = key.replace('_', ' ').title()
        
        if isinstance(value, dict):
            sections.append(f"{header_prefix} {formatted_key}")
            sections.append(dict_to_markdown_sections(value, level + 1))
        elif isinstance(value, list):
            sections.append(f"{header_prefix} {formatted_key}")
            if all(isinstance(item, dict) for item in value):
                sections.append(dict_list_to_md_table(value))
            else:
                sections.append(list_to_markdown(value))
        else:
            sections.append(f"**{formatted_key}:** {value}")
    
    return '\n\n'.join(filter(None, sections))


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
            # For dict items in a list, format as sub-items
            dict_parts = []
            for key, value in item.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, (dict, list)):
                    nested = convert_to_markdown(value)
                    dict_parts.append(f"  - **{formatted_key}:**\n    {nested}")
                else:
                    dict_parts.append(f"  - **{formatted_key}:** {value}")
            markdown_items.append("- " + "\n".join(dict_parts))
        elif isinstance(item, list):
            # For nested lists, indent
            nested = list_to_markdown(item)
            indented = '\n'.join(f"  {line}" for line in nested.split('\n'))
            markdown_items.append(indented)
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


def parse_multi_agent_response_to_markdown(raw_content: str) -> str:
    """
    Elaborate function to parse concatenated multi-agent responses into clean, structured Markdown.
    Handles JSON objects, agent headers, and complex nested structures.

    Args:
        raw_content: The raw string content from the response file.

    Returns:
        str: Clean Markdown-formatted output.
    """
    try:
        markdown_parts = []
        
        # Split content by agent headers (e.g., "## Agent Name")
        agent_sections = re.split(r'(^## .+$)', raw_content, flags=re.MULTILINE)
        
        # Process each section
        for i, section in enumerate(agent_sections):
            section = section.strip()
            if not section:
                continue
                
            # If this is an agent header, add it
            if section.startswith('##'):
                markdown_parts.append(section)
                continue
            
            # Try to parse as JSON
            try:
                json_data = json.loads(section)
                markdown_parts.append(json_to_markdown(json_data))
            except json.JSONDecodeError:
                # Not valid JSON, try to process as text
                # Check if it contains JSON-like structures
                json_objects = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', section, re.DOTALL)
                
                if json_objects:
                    for json_str in json_objects:
                        try:
                            json_data = json.loads(json_str)
                            markdown_parts.append(json_to_markdown(json_data))
                        except json.JSONDecodeError:
                            markdown_parts.append(ensure_markdown_formatting(json_str))
                else:
                    # Just plain text
                    if section.strip():
                        markdown_parts.append(ensure_markdown_formatting(section))
        
        # Filter out empty parts and join
        return '\n\n'.join(filter(None, markdown_parts))
        
    except Exception as e:
        logger.error(f"Error parsing multi-agent response to markdown: {e}")
        return ensure_markdown_formatting(raw_content)


def json_to_markdown_with_tables(data: Union[Dict[str, Any], List[Any]]) -> str:
    """
    Extended JSON to Markdown converter with table handling for lists of dicts.
    
    Args:
        data: JSON data (dict or list)
        
    Returns:
        str: Markdown string
    """
    if isinstance(data, list):
        if all(isinstance(item, dict) for item in data):
            return dict_list_to_md_table(data)
        else:
            return list_to_markdown(data)
    elif isinstance(data, dict):
        return json_to_markdown(data)
    else:
        return str(data)


def dict_list_to_md_table(items: List[Dict[str, Any]]) -> str:
    """
    Convert a list of dictionaries to a Markdown table.
    
    Args:
        items: List of dicts with consistent keys
        
    Returns:
        str: Markdown table
    """
    if not items:
        return ""
    
    # Get all unique keys from all items
    all_keys = []
    for item in items:
        for key in item.keys():
            if key not in all_keys:
                all_keys.append(key)
    
    # Create table header
    headers = all_keys
    table = ["| " + " | ".join(headers) + " |"]
    table.append("|" + " --- |" * len(headers))
    
    # Create table rows
    for item in items:
        row = []
        for key in headers:
            value = item.get(key, "")
            if isinstance(value, (dict, list)):
                # Format nested structures compactly for table cells
                if isinstance(value, dict):
                    nested_items = []
                    for k, v in value.items():
                        nested_items.append(f"**{k}:** {v}")
                    value = "<br>".join(nested_items)
                else:
                    value = "<br>".join(str(v) for v in value)
            # Clean up value for table cell
            value_str = str(value).replace('\n', '<br>').replace('|', '\\|')
            row.append(value_str)
        table.append("| " + " | ".join(row) + " |")
    
    return '\n'.join(table)
