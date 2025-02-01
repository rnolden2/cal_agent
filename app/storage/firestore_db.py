from typing import Union
import logging
from google.cloud import firestore
import orjson

from ..agent_schema.agent_master_schema import DatabaseModel, UpdateAgentRequest
from ..agents.cal_master.json_schema import json_schema_master
from ..agents.customer_connect.json_schema import json_schema_customer_connect
from ..agents.doc_master.json_schema import json_schema_doc_master
from ..agents.editor.json_schema import json_schema_editor
from ..agents.engineer.json_schema import json_schema_engineer
from ..agents.pro_mentor.json_schema import json_schema_pro_mentor
from ..agents.rival_watcher.json_schema import json_schema_rival_watcher
from ..agents.sales_agent.json_schema import json_schema_sales_agent
from ..agents.tech_wiz.json_schema import json_schema_tech_wiz
from ..agents.trend_tracker.json_schema import json_schema_trend_tracker
from ..config.agent_list import AgentDescriptions, master_agent_description_prompt

# Initialize Firestore client
database = "cal-project"
db = firestore.Client(database=database)
logger = logging.getLogger(__name__)


def store_agent_response(response: DatabaseModel) -> str:
    """Store new response in Firestore database"""
    try:
        # Reference to the Firestore collection
        collection_ref = db.collection("agent_responses")
        

        # Generate a custom document ID
        doc_ref = collection_ref.document()

        # Convert the TaskEvent object to a JSON string
        data = orjson.loads(response.content)

        # Set data in the document
        doc_ref.set(data)

        doc_id = doc_ref.id

        # Update document with agent info, response_id and timestamp
        update_data = {
            "agent": response.agent,
            "response_id": doc_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "topic_id": response.topic_id,
            "user_id": response.user_id,
        }

        doc_ref.update(update_data)
        print(f"Document created with ID: {doc_id}")
        print(f"Agent: {response.agent}")
        return doc_id
    # Handle any errors that occur during the Firestore operation
    except Exception as e:
        logger.error(f"Error writing to Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to write to database") from e


def create_topic_id():
    """Create a document ID used as a topic_id"""
    try:
        return db.collection("agent_responses").document().id
    except Exception as e:
        logger.error(f"Error creating Firestore document ID: {e}", exc_info=True)
        raise RuntimeError("Failed to create document ID") from e


def set_topic_id(topic_id: Union[str]) -> str:
    """Sets the topic_id if it's not provided in the request."""
    return topic_id if topic_id else create_topic_id()

def update_agent_document(agent_id: str, update_data: UpdateAgentRequest):
    try:
            # Reference the agent document in Firestore
        agent_ref = db.collection("agents").document(agent_id)

        # Check if the document exists
        if not agent_ref.get().exists:
            raise Exception(status_code=404, detail=f"Agent with ID '{agent_id}' does not exist.")

        # Convert Pydantic model to dictionary and remove None values
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}

        if not update_dict:
            raise Exception(status_code=400, detail="No valid data provided for update.")

        # Update the document with the provided data
        agent_ref.update(update_dict)

        return {"success": f"Agent '{agent_id}' updated successfully."}
    except Exception as e:
        logger.error(f"Error updating Firestore document: {e}", exc_info=True)
        raise RuntimeError("Failed to update Firestore document") from e

def create_agent_document(
    agent_name, api_route, description, description_full, role, schema
):
    """Create a Firestore document for an agent."""

    # Firestore document data
    agent_data = {
        "api_route": api_route,
        "description": description,
        "description_full": description_full,
        "last_updated": firestore.SERVER_TIMESTAMP,
        "role": role,
        "schema": schema,
    }

    # Create a document for the agent
    db.collection("agents").document(agent_name).set(agent_data)
    print(f"Document created for agent: {agent_name}")


agents = {
    "CUSTOMER_CONNECT": {
        "api_route": "/customerconnect",
        "description": "Assist in crafting professional, timely, and compliant customer communications.",
        "description_full": "Craft professional and compliant email communications, recommend optimal follow-ups, and ensure confidentiality in all customer interactions.",
        "role": AgentDescriptions.CUSTOMER_CONNECT.value,
        "schema": json_schema_customer_connect,
    },
    "DOC_MASTER": {
        "api_route": "/docmaster",
        "description": "Maintain, retrieve, and organize an up-to-date document library.",
        "description_full": "Organize and maintain a comprehensive document library, ensuring quick and efficient retrieval of technical papers, standards, and resources.",
        "role": AgentDescriptions.DOC_MASTER.value,
        "schema": json_schema_doc_master,
    },
    "MASTER_AGENT": {
        "api_route": "/master",
        "description": "Oversee and integrate operations of specialized agents for optimized outcomes.",
        "description_full": "Coordinate and manage the actions of all agents, ensuring efficient integration and optimization of workflows to achieve strategic objectives.",
        "role": master_agent_description_prompt,
        "schema": json_schema_master,
    },
    "ENGINEER_AGENT": {
        "api_route": "/engineer",
        "description": "Explain engineering fundamentals and enhance technical understanding for tasks.",
        "description_full": "Provide expert guidance on engineering concepts, principles, and resources to enhance understanding and improve technical task execution.",
        "role": AgentDescriptions.ENGINEER_AGENT.value,
        "schema": json_schema_engineer,
    },
    "EDITOR_AGENT": {
        "api_route": "/editor",
        "description": "Refine technical writing for clarity, brevity, and professional quality.",
        "description_full": "Edit technical writing to ensure clarity, brevity, and quality, adhering to professional standards and suggesting improvements for engagement and tone.",
        "role": AgentDescriptions.EDITOR_AGENT.value,
        "schema": json_schema_engineer,
    },
    "PRO_MENTOR": {
        "api_route": "/promentor",
        "description": "Provide personalized coaching for improved work performance and development.",
        "description_full": "Offer personalized coaching and actionable feedback to improve task prioritization, performance, and professional growth while building on past lessons.",
        "role": AgentDescriptions.PRO_MENTOR.value,
        "schema": json_schema_pro_mentor,
    },
    "RIVAL_WATCHER": {
        "api_route": "/rivalwatcher",
        "description": "Track competitors’ activities, updates, and insights for strategic decisions.",
        "description_full": "Continuously monitor and analyze competitor activities, providing detailed intelligence to support strategic planning and decision-making.",
        "role": AgentDescriptions.RIVAL_WATCHER.value,
        "schema": json_schema_rival_watcher,
    },
    "SALES_AGENT": {
        "api_route": "/sales",
        "description": "Develop actionable sales strategies tailored to government and defense clients.",
        "description_full": "Develop effective sales strategies for government and defense markets, identifying key decision-makers and uncovering untapped business opportunities.",
        "role": AgentDescriptions.SALES_AGENT.value,
        "schema": json_schema_sales_agent,
    },
    "TECH_WIZ": {
        "api_route": "/techwiz",
        "description": "Create clear, accurate technical content for proposals and presentations.",
        "description_full": "Create accurate and high-quality technical content, simplifying complex concepts for proposals, presentations, and reports while adhering to guidelines.",
        "role": AgentDescriptions.TECH_WIZ.value,
        "schema": json_schema_tech_wiz,
    },
    "TREND_TRACKER": {
        "api_route": "/trendtracker",
        "description": "Monitor market trends in hybridization and electrification for timely insights.",
        "description_full": "Regularly monitor and report on market trends, programs, and solicitations in military hybridization and electrification to inform strategic efforts.",
        "role": AgentDescriptions.TREND_TRACKER.value,
        "schema": json_schema_trend_tracker,
    },
}
