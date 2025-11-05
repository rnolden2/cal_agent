"""
Comprehensive test suite for Firestore database operations.
"""

import asyncio
import orjson
import uuid
import logging
from typing import Dict, Any
from datetime import datetime

from app.storage.firestore_db import (
    store_agent_response, 
    get_agent_responses,
    store_feedback_entry,
    get_feedback_entries,
    update_agent_document,
    create_topic_id,
    set_topic_id,
    delete_agent_response,
    delete_feedback_entry,
    delete_agent_document,
    db
)
from app.agent_schema.agent_master_schema import DatabaseModel, UpdateAgentRequest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirestoreTester:
    """Comprehensive test suite for all Firestore collections and operations."""

    def __init__(self):
        self.test_results = {
            "agent_responses_collection": {},
            "feedback_collection": {},
            "agents_collection_update": {},
            "topic_id_operations": {},
            "multiple_agent_responses": {},
            "edge_cases_error_handling": {},
            "concurrent_operations": {},
            "legacy_read_write": {}
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all Firestore tests and return a comprehensive report."""
        logger.info("Starting Firestore operations tests...")

        await self._test_agent_responses_collection()
        await self._test_feedback_collection()
        await self._test_agents_collection_update()
        self._test_topic_id_operations()
        await self._test_multiple_agent_responses_same_topic()
        await self._test_edge_cases_and_error_handling()
        await self._test_concurrent_operations()
        await self._test_firestore_read_write()

        test_report = self._generate_test_report()
        logger.info("Firestore operations tests completed!")
        return test_report

    async def _test_agent_responses_collection(self):
        """Test complete CRUD operations for agent_responses collection."""
        logger.info("Testing agent_responses collection...")
        response_id = None
        try:
            topic_id = f"test-topic-{uuid.uuid4()}"
            user_id = f"test-user-{uuid.uuid4()}"
            
            test_data = {
                "agent_name": "test_agent",
                "response": "This is a comprehensive test response.",
                "model": "gpt-4",
                "provider": "openai"
            }
            content = orjson.dumps(test_data).decode()
            
            response_id = await store_agent_response(
                content=content,
                user_id=user_id,
                agent_name="test_agent",
                topic_id=topic_id
            )
            assert response_id is not None
            
            await asyncio.sleep(1)
            
            retrieved_responses = await get_agent_responses(topic_id=topic_id, user_id=user_id, limit=1)
            assert len(retrieved_responses) == 1
            assert orjson.loads(retrieved_responses[0]['content']) == test_data
            
            self.test_results["agent_responses_collection"] = {"success": True, "message": "CRUD operations successful"}
        except Exception as e:
            logger.error(f"Agent responses collection test failed: {e}")
            self.test_results["agent_responses_collection"] = {"success": False, "error": str(e)}
        finally:
            if response_id:
                await delete_agent_response(response_id)

    async def _test_feedback_collection(self):
        """Test complete CRUD operations for feedback collection."""
        logger.info("Testing feedback collection...")
        feedback_id = None
        try:
            user_id = f"test-user-{uuid.uuid4()}"
            feedback_data = {
                "user_id": user_id, "rating": 5, "comment": "Excellent service",
                "category": "agent_performance", "agent_name": "test_agent",
                "session_id": f"session-{uuid.uuid4()}"
            }
            
            feedback_id = await store_feedback_entry(feedback_data)
            assert feedback_id is not None
            
            await asyncio.sleep(1)
            
            user_feedback = await get_feedback_entries(user_id=user_id, limit=5)
            assert len(user_feedback) >= 1
            assert user_feedback[0]["rating"] == 5
            
            self.test_results["feedback_collection"] = {"success": True, "message": "CRUD operations successful"}
        except Exception as e:
            logger.error(f"Feedback collection test failed: {e}")
            self.test_results["feedback_collection"] = {"success": False, "error": str(e)}
        finally:
            if feedback_id:
                await delete_feedback_entry(feedback_id)

    async def _test_agents_collection_update(self):
        """Test UPDATE operations for agents collection."""
        logger.info("Testing agents collection update...")
        agent_id = f"test-agent-{uuid.uuid4()}"
        try:
            # Create a dummy agent to update and then delete
            db.collection("agents").document(agent_id).set({"name": "dummy_agent"})
            
            update_data = UpdateAgentRequest(
                api_route="/api/test-agent", description="Updated description",
                description_full="Full description", role="test_assistant",
                agent_schema='{"type": "test"}'
            )
            
            update_agent_document(agent_id, update_data)
            
            self.test_results["agents_collection_update"] = {"success": True, "message": "Update logic tested"}
        except Exception as e:
            logger.error(f"Agents collection update test failed: {e}")
            self.test_results["agents_collection_update"] = {"success": False, "error": str(e)}
        finally:
            delete_agent_document(agent_id)

    def _test_topic_id_operations(self):
        """Test topic ID creation and setting operations."""
        logger.info("Testing topic ID operations...")
        try:
            topic_id = create_topic_id()
            assert topic_id is not None
            
            existing_topic = "existing-topic-123"
            assert set_topic_id(existing_topic) == existing_topic
            assert set_topic_id(None) is not None
            
            self.test_results["topic_id_operations"] = {"success": True, "message": "Creation and setting successful"}
        except Exception as e:
            logger.error(f"Topic ID operations test failed: {e}")
            self.test_results["topic_id_operations"] = {"success": False, "error": str(e)}

    async def _test_multiple_agent_responses_same_topic(self):
        """Test storing and retrieving multiple responses for the same topic."""
        logger.info("Testing multiple agent responses for the same topic...")
        response_ids = []
        try:
            topic_id = f"multi-test-topic-{uuid.uuid4()}"
            user_id = f"multi-test-user-{uuid.uuid4()}"
            agents = ["agent_1", "agent_2", "agent_3"]
            
            for i, agent_name in enumerate(agents):
                content = orjson.dumps({"agent_name": agent_name, "sequence": i}).decode()
                
                response_id = await store_agent_response(
                    content=content,
                    user_id=user_id,
                    agent_name=agent_name,
                    topic_id=topic_id
                )
                response_ids.append(response_id)
            
            await asyncio.sleep(1)
            
            retrieved = await get_agent_responses(topic_id=topic_id, user_id=user_id, limit=10)
            assert len(retrieved) == 3
            
            self.test_results["multiple_agent_responses"] = {"success": True, "message": "Storage and retrieval successful"}
        except Exception as e:
            logger.error(f"Multiple agent responses test failed: {e}")
            self.test_results["multiple_agent_responses"] = {"success": False, "error": str(e)}
        finally:
            for response_id in response_ids:
                await delete_agent_response(response_id)

    async def _test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling scenarios."""
        logger.info("Testing edge cases and error handling...")
        response_ids = []
        feedback_ids = []
        try:
            # Empty content
            response_id = await store_agent_response(content="{}", user_id="u", agent_name="test", topic_id="t")
            response_ids.append(response_id)
            
            # Large content
            large_content = orjson.dumps({"response": "x" * 1000}).decode()
            response_id = await store_agent_response(
                content=large_content,
                user_id=f"l-{uuid.uuid4()}",
                agent_name="test",
                topic_id=f"l-{uuid.uuid4()}"
            )
            response_ids.append(response_id)
            
            # Minimal feedback
            feedback_id = await store_feedback_entry({"user_id": f"m-{uuid.uuid4()}", "rating": 1})
            feedback_ids.append(feedback_id)
            
            self.test_results["edge_cases_error_handling"] = {"success": True, "message": "Edge cases handled"}
        except Exception as e:
            logger.error(f"Edge cases test failed: {e}")
            self.test_results["edge_cases_error_handling"] = {"success": False, "error": str(e)}
        finally:
            for response_id in response_ids:
                await delete_agent_response(response_id)
            for feedback_id in feedback_ids:
                await delete_feedback_entry(feedback_id)

    async def _test_concurrent_operations(self):
        """Test concurrent read/write operations."""
        logger.info("Testing concurrent operations...")
        response_ids = []
        try:
            topic_id = f"concurrent-topic-{uuid.uuid4()}"
            user_id = f"concurrent-user-{uuid.uuid4()}"
            
            async def create_response(i):
                content = orjson.dumps({"agent": f"c_{i}"}).decode()
                response_id = await store_agent_response(
                    content=content,
                    user_id=user_id,
                    agent_name=f"agent_{i}",
                    topic_id=topic_id
                )
                response_ids.append(response_id)
            
            tasks = [create_response(i) for i in range(5)]
            await asyncio.gather(*tasks)
            
            await asyncio.sleep(2)
            
            retrieved = await get_agent_responses(topic_id=topic_id, user_id=user_id, limit=10)
            assert len(retrieved) == 5
            
            self.test_results["concurrent_operations"] = {"success": True, "message": "Concurrent operations successful"}
        except Exception as e:
            logger.error(f"Concurrent operations test failed: {e}")
            self.test_results["concurrent_operations"] = {"success": False, "error": str(e)}
        finally:
            for response_id in response_ids:
                await delete_agent_response(response_id)

    async def _test_firestore_read_write(self):
        """Legacy test for backward compatibility."""
        logger.info("Testing legacy firestore_read_write...")
        response_id = None
        try:
            topic_id = f"legacy-test-topic-{uuid.uuid4()}"
            user_id = f"legacy-test-user-{uuid.uuid4()}"
            test_data = {"agent_name": "test_agent", "response": "This is a test response."}
            content = orjson.dumps(test_data).decode()
            
            response_id = await store_agent_response(
                content=content,
                user_id=user_id,
                agent_name="test_agent",
                topic_id=topic_id
            )
            await asyncio.sleep(1)
            
            retrieved = await get_agent_responses(topic_id=topic_id, user_id=user_id, limit=1)
            assert len(retrieved) == 1
            assert orjson.loads(retrieved[0]['content']) == test_data
            
            self.test_results["legacy_read_write"] = {"success": True, "message": "Read/write successful"}
        except Exception as e:
            logger.error(f"Legacy read/write test failed: {e}")
            self.test_results["legacy_read_write"] = {"success": False, "error": str(e)}
        finally:
            if response_id:
                await delete_agent_response(response_id)

    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results.values() if r.get("success"))
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": round(success_rate, 2),
                "status": "PASSED" if success_rate == 100 else "FAILED"
            },
            "detailed_results": self.test_results,
            "timestamp": datetime.now().isoformat()
        }

async def run_firestore_tests() -> Dict[str, Any]:
    """Convenience function to run all Firestore tests."""
    tester = FirestoreTester()
    return await tester.run_all_tests()

if __name__ == "__main__":
    async def main():
        logger.info("Starting Firestore Operations Test Suite...")
        results = await run_firestore_tests()
        
        print("\n" + "="*60)
        print("Firestore Test Results Summary:")
        print(f"  Total Tests: {results['test_summary']['total_tests']}")
        print(f"  Successful: {results['test_summary']['successful_tests']}")
        print(f"  Success Rate: {results['test_summary']['success_rate']}%")
        print(f"  Overall Status: {results['test_summary']['status']}")
        print("="*60)
        
        if results['test_summary']['status'] != "PASSED":
            print("\nDetailed Failures:")
            for test, result in results['detailed_results'].items():
                if not result.get('success'):
                    print(f"  - {test}: {result.get('error', 'No error message')}")
            print("\n")

    asyncio.run(main())
