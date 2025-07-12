from typing import Union
import logging
from google.cloud import firestore
import orjson

from ..agent_schema.agent_master_schema import DatabaseModel, UpdateAgentRequest


# Initialize Firestore client
database = "cal-project"
db = firestore.Client(database=database)



async def store_agent_response(response: DatabaseModel) -> str:
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
            "response_id": doc_id,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "topic_id": response.topic_id,
            "user_id": response.user_id,
        }

        doc_ref.update(update_data)
        print(f"Document created with ID: {doc_id}")
        return doc_id
    # Handle any errors that occur during the Firestore operation
    except Exception as e:
        logging.error(f"Error writing to Firestore: {e}", exc_info=True)
        raise RuntimeError("Failed to write to database") from e


def create_topic_id():
    """Create a document ID used as a topic_id"""
    try:
        return db.collection("agent_responses").document().id
    except Exception as e:
        logging.error(f"Error creating Firestore document ID: {e}", exc_info=True)
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
        update_dict = {k: v for k, v in update_data.model_dump_json().items() if v is not None}

        if not update_dict:
            raise Exception(status_code=400, detail="No valid data provided for update.")

        # Update the document with the provided data
        agent_ref.update(update_dict)

        return {"success": f"Agent '{agent_id}' updated successfully."}
    except Exception as e:
        logging.error(f"Error updating Firestore document: {e}", exc_info=True)
        raise RuntimeError("Failed to update Firestore document") from e

