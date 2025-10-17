#!/usr/bin/env python3
"""
Troubleshooting utility for CAL agent responses.

This script helps identify and debug issues with stored responses in Firestore,
including empty content fields, corrupted data patterns, and storage errors.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..storage.firestore_db import db, get_agent_responses
from ..agent_schema.agent_master_schema import Provider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResponseTroubleshooter:
    """Utility class for troubleshooting agent response storage issues."""
    
    def __init__(self):
        self.corrupted_patterns = [
            '{"type":"object","properties":{},"data":{}}',
            '{"type":"object","properties":{}}',
            'type object properties'
        ]
    
    async def analyze_response_health(self, limit: int = 100, days_back: int = 7) -> Dict[str, Any]:
        """
        Analyze the health of stored responses.
        
        Args:
            limit: Maximum number of responses to analyze
            days_back: How many days back to analyze
            
        Returns:
            Dict containing analysis results
        """
        logger.info(f"Analyzing response health for last {days_back} days (max {limit} responses)")
        
        try:
            # Get recent responses
            responses = await get_agent_responses(limit=limit)
            
            analysis = {
                "total_responses": len(responses),
                "healthy_responses": 0,
                "empty_content": 0,
                "corrupted_content": 0,
                "unknown_status": 0,
                "missing_llm_info": 0,
                "corrupted_responses": [],
                "error_responses": [],
                "llm_provider_stats": {},
                "agent_stats": {},
                "content_length_stats": {
                    "min": float('inf'),
                    "max": 0,
                    "avg": 0,
                    "total": 0
                }
            }
            
            total_length = 0
            
            for response in responses:
                content = response.get("content", "")
                content_status = response.get("content_status", "unknown")
                agent_name = response.get("agent_name", "Unknown")
                llm_provider = response.get("llm_provider")
                llm_model = response.get("llm_model")
                content_length = response.get("content_length", len(content) if content else 0)
                
                # Count by status
                if content_status == "valid":
                    analysis["healthy_responses"] += 1
                elif content_status == "error":
                    analysis["error_responses"].append(response)
                else:
                    analysis["unknown_status"] += 1
                
                # Check for empty content
                if not content or content.strip() == "":
                    analysis["empty_content"] += 1
                    analysis["corrupted_responses"].append({
                        "response_id": response.get("response_id"),
                        "agent_name": agent_name,
                        "issue": "empty_content",
                        "content": content[:100] if content else "None",
                        "timestamp": response.get("timestamp")
                    })
                
                # Check for corrupted patterns
                elif any(pattern.lower() in content.lower() for pattern in self.corrupted_patterns):
                    analysis["corrupted_content"] += 1
                    analysis["corrupted_responses"].append({
                        "response_id": response.get("response_id"),
                        "agent_name": agent_name,
                        "issue": "corrupted_pattern",
                        "content": content[:200],
                        "timestamp": response.get("timestamp")
                    })
                
                # Check for missing LLM info
                if not llm_provider or not llm_model:
                    analysis["missing_llm_info"] += 1
                
                # LLM provider stats
                if llm_provider:
                    if llm_provider not in analysis["llm_provider_stats"]:
                        analysis["llm_provider_stats"][llm_provider] = 0
                    analysis["llm_provider_stats"][llm_provider] += 1
                
                # Agent stats
                if agent_name not in analysis["agent_stats"]:
                    analysis["agent_stats"][agent_name] = {"count": 0, "avg_length": 0, "issues": 0}
                analysis["agent_stats"][agent_name]["count"] += 1
                
                # Content length stats
                if content_length > 0:
                    total_length += content_length
                    analysis["content_length_stats"]["min"] = min(analysis["content_length_stats"]["min"], content_length)
                    analysis["content_length_stats"]["max"] = max(analysis["content_length_stats"]["max"], content_length)
                
                # Track issues per agent
                if content_status == "error" or not content or any(pattern.lower() in content.lower() for pattern in self.corrupted_patterns):
                    analysis["agent_stats"][agent_name]["issues"] += 1
            
            # Calculate averages
            if analysis["total_responses"] > 0:
                analysis["content_length_stats"]["avg"] = total_length / analysis["total_responses"]
                analysis["content_length_stats"]["total"] = total_length
                
                # Fix infinite min value
                if analysis["content_length_stats"]["min"] == float('inf'):
                    analysis["content_length_stats"]["min"] = 0
                
                # Calculate agent averages
                for agent_stats in analysis["agent_stats"].values():
                    if agent_stats["count"] > 0:
                        agent_stats["issue_rate"] = agent_stats["issues"] / agent_stats["count"]
            
            logger.info(f"Analysis complete: {analysis['healthy_responses']}/{analysis['total_responses']} healthy responses")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing response health: {e}")
            raise
    
    async def get_storage_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent storage errors from the storage_errors collection.
        
        Args:
            limit: Maximum number of errors to retrieve
            
        Returns:
            List of error documents
        """
        try:
            query = db.collection("storage_errors")
            query = query.order_by("timestamp", direction=db.Query.DESCENDING).limit(limit)
            
            errors = []
            for doc in query.stream():
                error_data = doc.to_dict()
                errors.append(error_data)
            
            logger.info(f"Retrieved {len(errors)} storage errors")
            return errors
            
        except Exception as e:
            logger.error(f"Error retrieving storage errors: {e}")
            return []
    
    async def validate_llm_tracking(self, limit: int = 50) -> Dict[str, Any]:
        """
        Validate that LLM tracking information is being stored correctly.
        
        Args:
            limit: Number of responses to check
            
        Returns:
            Dict with validation results
        """
        try:
            responses = await get_agent_responses(limit=limit)
            
            validation = {
                "total_checked": len(responses),
                "with_llm_info": 0,
                "missing_provider": 0,
                "missing_model": 0,
                "valid_providers": set(),
                "provider_distribution": {},
                "model_distribution": {},
                "issues": []
            }
            
            valid_providers = {provider.value for provider in Provider}
            
            for response in responses:
                llm_provider = response.get("llm_provider")
                llm_model = response.get("llm_model")
                response_id = response.get("response_id", "unknown")
                agent_name = response.get("agent_name", "unknown")
                
                if llm_provider and llm_model:
                    validation["with_llm_info"] += 1
                    
                    # Track provider distribution
                    if llm_provider not in validation["provider_distribution"]:
                        validation["provider_distribution"][llm_provider] = 0
                    validation["provider_distribution"][llm_provider] += 1
                    
                    # Track model distribution
                    if llm_model not in validation["model_distribution"]:
                        validation["model_distribution"][llm_model] = 0
                    validation["model_distribution"][llm_model] += 1
                    
                    # Validate provider
                    if llm_provider in valid_providers:
                        validation["valid_providers"].add(llm_provider)
                    else:
                        validation["issues"].append({
                            "response_id": response_id,
                            "agent_name": agent_name,
                            "issue": "invalid_provider",
                            "provider": llm_provider
                        })
                
                else:
                    if not llm_provider:
                        validation["missing_provider"] += 1
                    if not llm_model:
                        validation["missing_model"] += 1
                    
                    validation["issues"].append({
                        "response_id": response_id,
                        "agent_name": agent_name,
                        "issue": "missing_llm_info",
                        "provider": llm_provider,
                        "model": llm_model
                    })
            
            # Convert sets to lists for JSON serialization
            validation["valid_providers"] = list(validation["valid_providers"])
            
            logger.info(f"LLM validation complete: {validation['with_llm_info']}/{validation['total_checked']} have LLM info")
            return validation
            
        except Exception as e:
            logger.error(f"Error validating LLM tracking: {e}")
            raise
    
    def print_analysis_report(self, analysis: Dict[str, Any]):
        """Print a formatted analysis report."""
        print("\n" + "="*80)
        print("CAL RESPONSE HEALTH ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Responses: {analysis['total_responses']}")
        print(f"   Healthy Responses: {analysis['healthy_responses']} ({analysis['healthy_responses']/analysis['total_responses']*100:.1f}%)")
        print(f"   Empty Content: {analysis['empty_content']}")
        print(f"   Corrupted Content: {analysis['corrupted_content']}")
        print(f"   Error Responses: {len(analysis['error_responses'])}")
        print(f"   Missing LLM Info: {analysis['missing_llm_info']}")
        
        print(f"\n📏 CONTENT LENGTH STATS:")
        print(f"   Minimum: {analysis['content_length_stats']['min']} chars")
        print(f"   Maximum: {analysis['content_length_stats']['max']} chars")
        print(f"   Average: {analysis['content_length_stats']['avg']:.1f} chars")
        print(f"   Total: {analysis['content_length_stats']['total']} chars")
        
        print(f"\n🤖 LLM PROVIDER DISTRIBUTION:")
        for provider, count in analysis['llm_provider_stats'].items():
            print(f"   {provider}: {count} responses ({count/analysis['total_responses']*100:.1f}%)")
        
        print(f"\n👥 AGENT PERFORMANCE:")
        for agent, stats in analysis['agent_stats'].items():
            issue_rate = stats.get('issue_rate', 0) * 100
            print(f"   {agent}: {stats['count']} responses, {stats['issues']} issues ({issue_rate:.1f}% issue rate)")
        
        if analysis['corrupted_responses']:
            print(f"\n⚠️  CORRUPTED RESPONSES ({len(analysis['corrupted_responses'])}):")
            for corrupt in analysis['corrupted_responses'][:5]:  # Show first 5
                print(f"   - {corrupt['agent_name']} ({corrupt['issue']}): {corrupt['content'][:50]}...")
            if len(analysis['corrupted_responses']) > 5:
                print(f"   ... and {len(analysis['corrupted_responses']) - 5} more")
        
        print("\n" + "="*80)
    
    def print_llm_validation_report(self, validation: Dict[str, Any]):
        """Print a formatted LLM validation report."""
        print("\n" + "="*80)
        print("LLM TRACKING VALIDATION REPORT")
        print("="*80)
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Checked: {validation['total_checked']}")
        print(f"   With LLM Info: {validation['with_llm_info']} ({validation['with_llm_info']/validation['total_checked']*100:.1f}%)")
        print(f"   Missing Provider: {validation['missing_provider']}")
        print(f"   Missing Model: {validation['missing_model']}")
        
        print(f"\n🔧 PROVIDER DISTRIBUTION:")
        for provider, count in validation['provider_distribution'].items():
            print(f"   {provider}: {count} responses")
        
        print(f"\n📱 MODEL DISTRIBUTION:")
        for model, count in validation['model_distribution'].items():
            print(f"   Model {model}: {count} responses")
        
        if validation['issues']:
            print(f"\n⚠️  ISSUES ({len(validation['issues'])}):")
            for issue in validation['issues'][:10]:  # Show first 10
                print(f"   - {issue['agent_name']} ({issue['response_id'][:8]}...): {issue['issue']}")
            if len(validation['issues']) > 10:
                print(f"   ... and {len(validation['issues']) - 10} more")
        
        print("\n" + "="*80)


async def main():
    """Main troubleshooting function."""
    troubleshooter = ResponseTroubleshooter()
    
    print("Starting CAL Response Troubleshooting Analysis...")
    
    try:
        # Run health analysis
        print("\n1. Analyzing response health...")
        analysis = await troubleshooter.analyze_response_health(limit=200, days_back=7)
        troubleshooter.print_analysis_report(analysis)
        
        # Validate LLM tracking
        print("\n2. Validating LLM tracking...")
        llm_validation = await troubleshooter.validate_llm_tracking(limit=100)
        troubleshooter.print_llm_validation_report(llm_validation)
        
        # Check storage errors
        print("\n3. Checking storage errors...")
        storage_errors = await troubleshooter.get_storage_errors(limit=20)
        
        if storage_errors:
            print(f"\n⚠️  RECENT STORAGE ERRORS ({len(storage_errors)}):")
            for error in storage_errors[:5]:
                print(f"   - {error.get('agent_name', 'Unknown')}: {error.get('error_message', 'No message')[:50]}...")
                print(f"     Content preview: {error.get('content', 'None')[:50]}...")
                print(f"     LLM: {error.get('llm_provider', 'Unknown')}/{error.get('llm_model', 'Unknown')}")
                print()
        else:
            print("✅ No recent storage errors found")
        
        print("\n✨ Troubleshooting analysis complete!")
        
    except Exception as e:
        logger.error(f"Error during troubleshooting: {e}")
        print(f"❌ Error during analysis: {e}")


if __name__ == "__main__":
    asyncio.run(main())
