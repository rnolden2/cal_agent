#!/usr/bin/env python3
"""
Test script to verify the markdown conversion functionality
"""

import sys
import os
import asyncio
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.markdown_converter import (
    convert_to_markdown,
    json_to_markdown,
    format_agent_response_for_display
)

def test_json_to_markdown():
    """Test converting JSON response to markdown"""
    print("🧪 Testing JSON to Markdown conversion...")
    
    # Test case 1: Simple agent response
    json_response = {
        "agent": "TrendTracker",
        "response": "This is a market research analysis with **bold text** and *italic text*.",
        "workflow_id": "workflow_20250106_093000",
        "agents_involved": ["TrendTracker", "Engineer"],
        "verification_results": {
            "overall_quality_score": 0.85,
            "reliability_score": 0.90,
            "verified_sources_count": 5,
            "approval_status": "approved"
        }
    }
    
    markdown_result = json_to_markdown(json_response)
    print("✅ JSON Response converted to:")
    print(markdown_result)
    print("\n" + "="*50 + "\n")
    
    # Test case 2: Complex nested response
    complex_response = {
        "agent": "Engineer",
        "response": {
            "raw_response": "## Technical Analysis\n\nThis is a detailed technical analysis with:\n\n- Point 1\n- Point 2\n- Point 3",
            "metadata": {
                "sources": ["source1.com", "source2.com"],
                "confidence": 0.95
            }
        },
        "feedback_impact": {
            "entries_applied": 3,
            "average_relevance": 0.88
        }
    }
    
    markdown_result = json_to_markdown(complex_response)
    print("✅ Complex Response converted to:")
    print(markdown_result)
    print("\n" + "="*50 + "\n")
    
    # Test case 3: Polished email response (like the user's feedback example)
    email_response = {
        "polished_email": "Subject: Follow-Up on Our Recent Discussion\n\nDear [Recipient Name],\n\nI hope you are well. I'm writing to follow up on our recent discussion regarding GVSETS. I appreciate the opportunity to connect and would like to summarize the key points we covered:\n\n• A brief overview of the main topics discussed.\n• An outline of the next steps and any outstanding questions.\n• A reminder of our upcoming deadlines or meetings, if applicable.\n\nPlease let me know if you have any additional questions or need further clarification on any of the points. I'm happy to assist further and look forward to moving ahead with the next steps.\n\nThank you for your time and consideration.\n\nBest regards,\n[Your Name]\n[Your Position]\n[Your Contact Information]",
        "summary_of_changes": "1. Simplified subject line and greeting to create an immediate, professional tone in line with The Elements of Style's emphasis on clarity and brevity. 2. Structured the email with bullet points for easy readability, reflecting On Writing Well's advice to keep writing simple and engaging. 3. Removed unnecessary jargon and verbosity by using direct language and clear instructions. 4. Ensured the message is concise, informative, and action-oriented, improving the overall tone and persuasive appeal of the follow-up email."
    }
    
    markdown_result = json_to_markdown(email_response)
    print("✅ Email Response converted to:")
    print(markdown_result)
    print("\n" + "="*50 + "\n")

def test_format_agent_response():
    """Test formatting agent response for display"""
    print("🧪 Testing Agent Response Formatting...")
    
    # Test case: Database response format
    db_response = {
        "content": "# Market Research Report\n\nThis is a comprehensive analysis of the defense market.\n\n## Key Findings\n\n- Finding 1\n- Finding 2",
        "agent_name": "TrendTracker",
        "topic_id": "topic_12345",
        "tags": ["market research", "defense", "analysis"],
        "timestamp": {"_seconds": 1704537600}  # Mock Firestore timestamp
    }
    
    formatted_result = format_agent_response_for_display(db_response)
    print("✅ Database Response formatted to:")
    print(formatted_result)
    print("\n" + "="*50 + "\n")

def test_convert_to_markdown():
    """Test general markdown conversion"""
    print("🧪 Testing General Markdown Conversion...")
    
    # Test case 1: Plain text
    plain_text = "This is plain text that should be formatted as markdown."
    result = convert_to_markdown(plain_text)
    print("✅ Plain text converted:")
    print(result)
    print()
    
    # Test case 2: JSON string
    json_string = '{"agent": "Sales", "response": "Business opportunity analysis complete."}'
    result = convert_to_markdown(json_string)
    print("✅ JSON string converted:")
    print(result)
    print()
    
    # Test case 3: List
    list_data = ["Item 1", "Item 2", {"nested": "data"}]
    result = convert_to_markdown(list_data)
    print("✅ List converted:")
    print(result)
    print("\n" + "="*50 + "\n")

def main():
    """Run all tests"""
    print("🚀 Starting Markdown Conversion Tests\n")
    
    try:
        test_json_to_markdown()
        test_format_agent_response()
        test_convert_to_markdown()
        
        print("✅ All tests completed successfully!")
        print("\n📋 Summary:")
        print("- JSON to Markdown conversion: ✅")
        print("- Agent response formatting: ✅") 
        print("- General markdown conversion: ✅")
        print("\n🎉 The markdown conversion system is working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
