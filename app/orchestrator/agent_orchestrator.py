"""
Unified orchestration system for the CAL application.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

from ..agent_schema.agent_master_schema import AgentCallModel, AgentModel, Provider
from ..context.feedback_manager import FeedbackContextManager
from ..context.feedback_impact_tracker import FeedbackImpactTracker
from ..verification.fact_verifier import FactVerificationEngine
from ..verification.quality_assurance import QualityAssuranceSystem
from ..orchestrator.agent_capabilities import (
    get_agents_for_task, get_agent_capabilities, get_collaboration_agents,
    requires_fact_verification, AGENT_CAPABILITIES
)
from ..llm.manager import callModel
from ..storage.firestore_db import store_agent_response, create_topic_id
from ..config.agent_list import AgentDescriptions
from ..agents.customer_connect.json_schema import json_schema_customer_connect
from ..agents.trend_tracker.json_schema import json_schema_trend_tracker
from ..agents.rival_watcher.json_schema import json_schema_rival_watcher
from ..agents.engineer.json_schema import json_schema_engineer
from ..agents.sales_agent.json_schema import json_schema_sales_agent
from ..agents.editor.json_schema import json_schema_editor
from ..agents.tech_wiz.json_schema import json_schema_tech_wiz
from ..agents.doc_master.json_schema import json_schema_doc_master
from ..agents.pro_mentor.json_schema import json_schema_pro_mentor
from ..agents.general.json_schema import json_schema_general
import asyncio

logger = logging.getLogger(__name__)

class UnifiedAgentRequest:
    """Request model for unified agent processing"""
    def __init__(self, task_type: str, content: str, user_id: str, 
                 agents_requested: Optional[List[str]] = None,
                 verification_required: bool = False,
                 feedback_context: bool = True,
                 additional_context: Optional[str] = None,
                 topic_id: Optional[str] = None):
        self.task_type = task_type
        self.content = content
        self.user_id = user_id
        self.agents_requested = agents_requested or []
        self.verification_required = verification_required
        self.feedback_context = feedback_context
        self.additional_context = additional_context
        self.topic_id = topic_id

class AgentResponse:
    """Response model for agent processing"""
    def __init__(self, content: str, agents_involved: List[str], 
                 workflow_id: str, quality_score: float = 0.0,
                 verification_status: str = "pending",
                 feedback_applied: List[str] = None):
        self.content = content
        self.agents_involved = agents_involved
        self.workflow_id = workflow_id
        self.quality_score = quality_score
        self.verification_status = verification_status
        self.feedback_applied = feedback_applied or []

class AgentOrchestrator:
    """
    Unified orchestration system replacing individual agent endpoints
    """
    
    def __init__(self):
        self.feedback_manager = FeedbackContextManager()
        self.impact_tracker = FeedbackImpactTracker()
        self.fact_verifier = FactVerificationEngine()
        self.quality_assurance = QualityAssuranceSystem()
    
    async def process_request(self, request: AgentCallModel) -> Dict[str, Any]:
        """
        Process the request by orchestrating various agents and services.
        
        Args:
            request: AgentCallModel containing the user request
            
        Returns:
            Dict containing the orchestrated response
        """
        try:
            # 0. Generate or ensure topic_id for this response
            topic_id = self._ensure_topic_id(request.topic_id)
            request.topic_id = topic_id  # Ensure the request has the topic_id
            
            logger.info(f"Processing request with topic_id: {topic_id}")
            
            # 1. Analyze request and determine required agents
            task_type = self._analyze_task_type(request.response)
            required_agents = self._determine_required_agents(
                task_type, request.response
            )
            
            logger.info(f"Topic {topic_id}: Using agents {required_agents} for task type '{task_type}'")
            
            # 2. Inject relevant feedback context if requested
            enhanced_prompt = request.response
            feedback_applied = []
            feedback_entries = []  # Initialize feedback_entries to avoid scope issues
            
            if hasattr(request, 'feedback_context') and getattr(request, 'feedback_context', True):
                feedback_entries = await self.feedback_manager.get_relevant_feedback(
                    task_type=task_type,
                    agent_names=required_agents,
                    user_id=request.user_id,
                    current_content=request.response
                )
                
                if feedback_entries:
                    # Apply feedback context to the primary agent
                    primary_agent = required_agents[0] if required_agents else "General"
                    enhanced_prompt = self.feedback_manager.inject_feedback_context(
                        prompt=request.response,
                        feedback=feedback_entries,
                        agent_name=primary_agent
                    )
                    feedback_applied = [f.category for f in feedback_entries]
                    
                    logger.info(f"Applied {len(feedback_entries)} feedback entries to prompt for {primary_agent}")
            
            # 3. Execute collaborative workflow
            workflow_id = self._generate_workflow_id()
            agent_responses, agent_llm_info = await self._execute_collaborative_workflow(
                agents=required_agents,
                prompt=enhanced_prompt,
                request=request,
                workflow_id=workflow_id
            )
            
            # 4. Aggregate responses
            unified_response = self._aggregate_responses(agent_responses, required_agents)
            
            # 5. Perform fact verification and quality assurance (non-intrusive)
            # Check if verification is enabled (default True for backward compatibility)
            enable_verification = getattr(request, 'enable_verification', True)
            
            verification_required = (
                enable_verification and (
                    getattr(request, 'verification_required', False) or
                    any(requires_fact_verification(agent) for agent in required_agents)
                )
            )
            
            quality_assessment = None
            if verification_required:
                logger.info("Performing fact verification and quality assurance (informational mode)")
                quality_assessment = await self.quality_assurance.assess_content_quality(
                    content=unified_response,
                    context=f"Task: {task_type}, Agents: {', '.join(required_agents)}"
                )
                logger.info(f"Verification completed - Status: {quality_assessment.approval_status}, Score: {quality_assessment.overall_quality_score:.2f}")
                # NOTE: Verification is now purely informational and does not modify content
            elif not enable_verification:
                logger.info("Verification disabled by request configuration")
            
            # 6. Track feedback impact if feedback was applied
            impact_metric = None
            if feedback_entries:
                impact_metric = self.impact_tracker.track_feedback_application(
                    workflow_id=workflow_id,
                    user_id=request.user_id,
                    task_type=task_type,
                    agents_involved=required_agents,
                    feedback_entries=feedback_entries,
                    response_content=unified_response
                )
            
            # 7. Store individual agent responses for future feedback learning
            await self._store_individual_agent_responses(
                agent_responses=agent_responses,
                workflow_id=workflow_id,
                user_id=request.user_id,
                topic_id=getattr(request, 'topic_id', None),
                agent_llm_info=agent_llm_info
            )
            
            # 8. Return unified response with all metrics
            response_data = {
                "response": unified_response,
                "agents_involved": required_agents,
                "workflow_id": workflow_id,
                "topic_id": topic_id,
                "feedback_applied": feedback_applied,
                "task_type": task_type,
                "verification_performed": verification_required
            }
            
            # Add impact metrics if available
            if impact_metric:
                response_data["quality_score"] = impact_metric.response_quality_score
                response_data["feedback_impact"] = {
                    "entries_applied": impact_metric.feedback_entries_count,
                    "average_relevance": impact_metric.average_relevance_score,
                    "improvement_indicators": impact_metric.improvement_indicators
                }
            
            # Add verification metrics if available (informational only)
            if quality_assessment:
                response_data["verification_metrics"] = {
                    "enabled": True,
                    "overall_quality_score": quality_assessment.overall_quality_score,
                    "approval_status": quality_assessment.approval_status,
                    "reliability_score": quality_assessment.verification_result.reliability_score,
                    "verified_sources_count": len(quality_assessment.verification_result.verified_sources),
                    "broken_links_count": len(quality_assessment.verification_result.broken_links),
                    "broken_links": quality_assessment.verification_result.broken_links,
                    "verified_claims_count": len(quality_assessment.verification_result.verified_claims),
                    "unverified_claims_count": len(quality_assessment.verification_result.unverified_claims),
                    "quality_issues": quality_assessment.quality_issues,
                    "recommendations": quality_assessment.quality_recommendations,
                    "quality_metrics": quality_assessment.quality_metrics,
                    "verification_timestamp": quality_assessment.assessment_timestamp.isoformat()
                }
            else:
                response_data["verification_metrics"] = {
                    "enabled": False,
                    "message": "Verification not performed for this request"
                }
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error in process_request: {e}", exc_info=True)
            return {
                "response": f"Error processing request: {str(e)}",
                "agents_involved": ["General"],
                "workflow_id": "error",
                "feedback_applied": [],
                "task_type": "error"
            }
    
    def _analyze_task_type(self, content: str) -> str:
        """
        Analyze the content to determine the task type
        """
        content_lower = content.lower()
        
        # Market research indicators
        if any(keyword in content_lower for keyword in [
            "market research", "industry trends", "competitive analysis",
            "market analysis", "trends", "solicitations", "awards"
        ]):
            return "market_research"
        
        # Competitor analysis indicators
        if any(keyword in content_lower for keyword in [
            "competitor", "competition", "rival", "competitive landscape"
        ]):
            return "competitor_analysis"
        
        # Technical analysis indicators
        if any(keyword in content_lower for keyword in [
            "technical", "engineering", "system design", "technology",
            "specifications", "requirements"
        ]):
            return "technical_analysis"
        
        # Business strategy indicators
        if any(keyword in content_lower for keyword in [
            "business strategy", "sales", "opportunity", "revenue",
            "growth", "market opportunity"
        ]):
            return "business_strategy"
        
        # Customer communication indicators
        if any(keyword in content_lower for keyword in [
            "email", "communication", "customer", "client", "presentation"
        ]):
            return "customer_communication"
        
        # Document creation indicators
        if any(keyword in content_lower for keyword in [
            "document", "write", "create", "draft", "proposal", "report"
        ]):
            return "document_creation"
        
        # Professional development indicators
        if any(keyword in content_lower for keyword in [
            "professional development", "coaching", "mentor", "career",
            "improvement", "skills"
        ]):
            return "professional_development"
        
        return "general"
    
    def _determine_required_agents(self, task_type: str, content: str) -> List[str]:
        """
        Determine which agents are required for the task
        """
        # Get base agents for task type
        base_agents = get_agents_for_task(task_type)
        
        # Add collaboration agents if needed
        required_agents = set(base_agents)
        
        # For complex tasks, add collaborative agents
        if task_type in ["market_research", "competitor_analysis", "technical_analysis"]:
            for agent in base_agents:
                collaborators = get_collaboration_agents(agent)
                # Add up to 2 most relevant collaborators to avoid overwhelming
                required_agents.update(collaborators[:2])
        
        # Always include ProfessionalMentor for feedback integration
        # (as specified in the original master agent prompt)
        if "ProfessionalMentor" not in required_agents:
            required_agents.add("ProfessionalMentor")
        
        # Convert to list and limit to reasonable number
        agent_list = list(required_agents)[:4]  # Limit to 4 agents max
        
        return agent_list
    
    async def _execute_collaborative_workflow(self, 
                                            agents: List[str], 
                                            prompt: str,
                                            request: AgentCallModel,
                                            workflow_id: str) -> tuple[Dict[str, str], Dict[str, Dict]]:
        """
        Execute the collaborative workflow with multiple agents in parallel
        
        Returns:
            Tuple of (agent_responses, agent_llm_info)
        """
        agent_responses = {}
        agent_llm_info = {}
        
        async def execute_agent(agent_name):
            try:
                # Get agent description
                agent_description = self._get_agent_description(agent_name)
                
                # Create agent-specific prompt
                agent_prompt = self._create_agent_specific_prompt(
                    agent_name, prompt, agent_description
                )
                
                # Determine optimal provider and model for agent
                provider, model = self._determine_optimal_provider_model(agent_name, prompt)
                
                # Store LLM info for this agent
                agent_llm_info[agent_name] = {
                    "provider": provider.value,
                    "model": str(model)
                }
                
                # Get the proper schema for this agent
                agent_schema = self._get_agent_schema(agent_name)
                
                # Create AgentModel for the specific agent
                agent_model = AgentModel(
                    agent=agent_name,
                    role=agent_description,
                    content=agent_prompt,
                    agent_schema=agent_schema,
                    additional_context=request.additional_context,
                    model=model,
                    provider=provider.value,
                    topic_id=request.topic_id,
                    user_id=request.user_id
                )
                
                # Call the agent using the existing LLM manager
                response = await callModel(agent_model)
                logger.info(f"Agent {agent_name} completed for workflow {workflow_id} using {provider.value}/model-{model}")
                return agent_name, response
                
            except Exception as e:
                logger.error(f"Error executing agent {agent_name}: {e}")
                # Still track LLM info even if there was an error
                if agent_name not in agent_llm_info:
                    agent_llm_info[agent_name] = {
                        "provider": "error",
                        "model": "error"
                    }
                return agent_name, f"Error: {str(e)}"
        
        # Run agents in parallel with semaphore to limit concurrency (e.g., max 3 simultaneous)
        semaphore = asyncio.Semaphore(3)
        
        async def bounded_execute_agent(agent_name):
            async with semaphore:
                return await execute_agent(agent_name)
        
        tasks = [bounded_execute_agent(agent) for agent in agents]
        results = await asyncio.gather(*tasks)
        
        # Collect results
        for agent_name, response in results:
            agent_responses[agent_name] = response
        
        return agent_responses, agent_llm_info
    
    def _get_agent_description(self, agent_name: str) -> str:
        """
        Get the description/role for an agent
        """
        # Map agent names to their descriptions
        agent_mapping = {
            "CustomerConnect": AgentDescriptions.CUSTOMER_CONNECT.value,
            "TrendTracker": AgentDescriptions.TREND_TRACKER.value,
            "RivalWatcher": AgentDescriptions.RIVAL_WATCHER.value,
            "Engineer": AgentDescriptions.ENGINEER_AGENT.value,
            "Sales": AgentDescriptions.SALES_AGENT.value,
            "Editor": AgentDescriptions.EDITOR_AGENT.value,
            "TechWiz": AgentDescriptions.TECH_WIZ.value,
            "DocumentMaster": AgentDescriptions.DOC_MASTER.value,
            "ProfessionalMentor": AgentDescriptions.PRO_MENTOR.value,
            "General": AgentDescriptions.GENERAL.value
        }
        
        return agent_mapping.get(agent_name, AgentDescriptions.GENERAL.value)
    
    def _get_agent_schema(self, agent_name: str) -> Dict:
        """
        Get the JSON schema for an agent
        """
        # Map agent names to their schemas
        schema_mapping = {
            "CustomerConnect": json_schema_customer_connect,
            "TrendTracker": json_schema_trend_tracker,
            "RivalWatcher": json_schema_rival_watcher,
            "Engineer": json_schema_engineer,
            "Sales": json_schema_sales_agent,
            "Editor": json_schema_editor,
            "TechWiz": json_schema_tech_wiz,
            "DocumentMaster": json_schema_doc_master,
            "ProfessionalMentor": json_schema_pro_mentor,
            "General": json_schema_general
        }
        
        return schema_mapping.get(agent_name, json_schema_general)
    
    def _create_agent_specific_prompt(self, agent_name: str, prompt: str, agent_description: str) -> str:
        """
        Create an agent-specific prompt based on the agent's role
        """
        return f"""
{agent_description}

Task: {prompt}

Please provide your response based on your specific expertise and role. Focus on the aspects most relevant to your domain while considering the broader context of the request.
"""
    
    def _determine_optimal_provider_model(self, agent_name: str, prompt: str) -> tuple[Provider, int]:
        """
        Determine the optimal provider and model for an agent based on task complexity
        """
        # Simple tasks use model 0, complex tasks use model 1
        model = 0 if len(prompt) < 200 else 1
        
        # Provider selection based on agent type and task complexity
        if agent_name == "TrendTracker":
            return Provider.PERPLEXITY, model  # Best for research
        elif agent_name in ["Engineer", "TechWiz"] and model == 1:
            return Provider.GOOGLE, model  # Good for complex technical tasks
        else:
            return Provider.OPENAI, model  # Default for most tasks
    
    def _aggregate_responses(self, agent_responses: Dict[str, str], agents: List[str]) -> str:
        """
        Aggregate multiple agent responses into a unified response
        """
        if len(agent_responses) == 1:
            return list(agent_responses.values())[0]
        
        # Create structured response with sections for each agent
        aggregated_parts = []
        
        for agent_name in agents:
            if agent_name in agent_responses:
                agent_capability = get_agent_capabilities(agent_name)
                description = agent_capability.get("description", agent_name)
                
                aggregated_parts.append(f"## {description}\n")
                aggregated_parts.append(f"{agent_responses[agent_name]}\n")
        
        return "\n".join(aggregated_parts)
    
    async def _store_individual_agent_responses(self, agent_responses: Dict[str, str],
                                              workflow_id: str, user_id: str, 
                                              topic_id: Optional[str] = None,
                                              agent_llm_info: Optional[Dict[str, Dict]] = None):
        """
        Store individual agent responses for future learning and UI display
        """
        try:
            stored_count = 0
            for agent_name, response_content in agent_responses.items():
                # Get LLM information for this agent if available
                llm_provider = None
                llm_model = None
                
                if agent_llm_info and agent_name in agent_llm_info:
                    llm_info = agent_llm_info[agent_name]
                    llm_provider = llm_info.get("provider")
                    llm_model = llm_info.get("model")
                
                # Store each agent response as a separate document
                doc_id = await store_agent_response(
                    content=response_content,
                    user_id=user_id,
                    agent_name=agent_name,
                    topic_id=topic_id,
                    llm_provider=llm_provider,
                    llm_model=llm_model
                )
                stored_count += 1
                logger.info(f"Stored response for agent {agent_name} with doc_id: {doc_id}, LLM: {llm_provider}/{llm_model}")
            
            logger.info(f"Stored {stored_count} individual agent responses for workflow {workflow_id}")
            
        except Exception as e:
            logger.error(f"Error storing individual agent responses: {e}")
    
    
    def _ensure_topic_id(self, topic_id: Optional[str]) -> str:
        """
        Ensure a topic_id exists for this response.
        If one is provided, use it. Otherwise, generate a new one.
        
        Args:
            topic_id: Optional existing topic_id
            
        Returns:
            str: The topic_id to use for this response
        """
        if topic_id:
            logger.info(f"Using existing topic_id: {topic_id}")
            return topic_id
        
        # Generate new topic_id using Firestore's document ID generator
        new_topic_id = create_topic_id()
        logger.info(f"Generated new topic_id: {new_topic_id}")
        return new_topic_id
    
    def _generate_workflow_id(self) -> str:
        """
        Generate a unique workflow ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"workflow_{timestamp}"
