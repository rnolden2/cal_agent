from typing import Union, List, Optional
import logging
from google.cloud import firestore
import orjson
import asyncio

from ..agent_schema.agent_master_schema import DatabaseModel, UpdateAgentRequest

# Initialize Firestore client
database = "cal-project"
db = firestore.Client(database=database)

async def store_agent_response(response: DatabaseModel) -> str:
    """Store new response in Firestore database."""
    try:
        col = db.collection("agent_responses")
        doc_ref = col.document()
        # assuming response.content is a JSON string
        data = orjson.loads(response.content)
        doc_ref.set(data)
        doc_id = doc_ref.id
        update_data = {
            "response_id": doc_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "topic_id": response.topic_id,
            "user_id": response.user_id,
        }
        doc_ref.update(update_data)
        logging.info(f"Document created with ID: {doc_id}")
        return doc_id
    except Exception as e:
        logging.error(f"Error writing to Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to write to database") from e

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
) -> List[DatabaseModel]:
    """
    Fetch agent_responses from Firestore, optionally filtered by topic_id and/or user_id.
    Returns up to `limit` items, ordered by timestamp descending.
    """
    def _query():
        # Start with the base collection
        query = db.collection("agent_responses")

        # Apply filters if they are provided
        if topic_id:
            query = query.where("topic_id", "==", topic_id)
        if user_id:
            query = query.where("user_id", "==", user_id)

        # Order by timestamp descending to get the most recent responses, and limit the result size.
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
        return [doc.to_dict() for doc in query.stream()]

    try:
        docs = await asyncio.to_thread(_query)
        responses: List[DatabaseModel] = []
        for d in docs:
            # Build content JSON string again if needed
            content_str = orjson.dumps({
                k: v for k, v in d.items() if k not in {"response_id", "timestamp", "topic_id", "user_id"}
            }).decode()
            responses.append(
                DatabaseModel(
                    content=content_str,
                    topic_id=d.get("topic_id"),
                    user_id=d.get("user_id"),
                )
            )
        return responses
    except Exception as e:
        logging.error(f"Error reading from Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to read responses from database") from e
