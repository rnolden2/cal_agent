# import asyncio
# import time
# import orjson
# from typing import List
# from ...agents import (
#     CustomerConnect,
#     DocMaster,
#     EditorAgent,
#     EngineerAgent,
#     ProMentor,
#     SalesAgent,
#     RivalWatcher,
#     TechWiz,
#     TrendTracker,
# )
# from .pydantic_schema import AgentTask
# from ...llm.manager import callModel
# from ...agent_schema.agent_master_schema import AgentModel, Provider
# from ...config.agent_list import AgentDescriptions, master_agent_description_prompt
# from .json_schema import json_schema_master
# from ...storage.firestore_db import set_topic_id

# class MasterAgent:
#     # Create prompt
#     def create_prompt(prompt: str) -> AgentModel:
#         schema_to_use = json_schema_master
#         agent_model = AgentModel(
#             role=master_agent_description_prompt,
#             content=prompt,
#             agent_schema=schema_to_use,
#             agent=AgentDescriptions.MASTER_AGENT.name,
#         )
#         return agent_model

#     # Make call and recieve back all agent prompts with their dependencies
#     async def call_model(agent_data: AgentModel, topic_id: str, user_id: str) ->List[AgentTask]:
#         agent_data.topic_id, agent_data.user_id = set_topic_id(topic_id), user_id
#         master_agent_call = await callModel(agent=agent_data, provider=Provider.GOOGLE, model=3)
#         response_dict = orjson.loads(master_agent_call)
#         agent_data = response_dict["response"]["tasks"]
#         tasks: List[AgentTask] = [AgentTask(**task) for task in agent_data]
#         return tasks
    
#     # Internal helper that performs processing for a single task.
#     async def _process_task(task: AgentTask, cache: Dict[str, asyncio.Task]) -> Any:
#         # First, ensure that any dependencies (dependents) are processed.
#         if task.dependents:
#             # Process all dependencies concurrently.
#             await asyncio.gather(*(process_task(dep, cache) for dep in task.dependents))
        
#         # Process the task itself.
#         result = await task.process()
#         return result

#     # Recursively processes a task, caching the result to avoid duplicate processing.
#     async def process_task(task: AgentTask, cache: Dict[str, asyncio.Task]) -> Any:
#         # If this task is already being processed or has been processed, reuse its result.
#         if task.name in cache:
#             return await cache[task.name]
        
#         # Otherwise, schedule processing and store the task in the cache.
#         task_future = asyncio.create_task(_process_task(task, cache))
#         cache[task.name] = task_future
#         return await task_future

#     # Setup agent queue separate calls that have dependencies and calls that don't
#     async def process_agent_queue(tasks: List[AgentTask]):
#         cache: Dict[str, asyncio.Task] = {}
                
#         # Process all top-level tasks concurrently.
#         results = await asyncio.gather(*(process_task(task, cache) for task in tasks))
#         return results
            
#     # Make all agent calls



# from typing import List, Dict, Any

# # Example Task class for context (you might already have your own task definition)
# class Task:
#     def __init__(self, name: str, dependents: List["Task"] = None):
#         self.name = name
#         # List of tasks that this task depends on.
#         self.dependents = dependents or []
    
#     async def process(self) -> Any:
#         # Simulate work with async sleep (replace with actual work)
#         print(f"Processing {self.name}")
#         await asyncio.sleep(1)
#         print(f"Finished processing {self.name}")
#         return f"Result of {self.name}"

# # Internal helper that performs processing for a single task.
# async def _process_task(task: Task, cache: Dict[str, asyncio.Task]) -> Any:
#     # First, ensure that any dependencies (dependents) are processed.
#     if task.dependents:
#         # Process all dependencies concurrently.
#         await asyncio.gather(*(process_task(dep, cache) for dep in task.dependents))
    
#     # Process the task itself.
#     result = await task.process()
#     return result

# # Recursively processes a task, caching the result to avoid duplicate processing.
# async def process_task(task: Task, cache: Dict[str, asyncio.Task]) -> Any:
#     # If this task is already being processed or has been processed, reuse its result.
#     if task.name in cache:
#         return await cache[task.name]
    
#     # Otherwise, schedule processing and store the task in the cache.
#     task_future = asyncio.create_task(_process_task(task, cache))
#     cache[task.name] = task_future
#     return await task_future

# # Main function that accepts a list of tasks and processes them asynchronously.
# async def process_agent_queue(tasks: List[Task]) -> List[Any]:
#     cache: Dict[str, asyncio.Task] = {}
#     # Process all top-level tasks concurrently.
#     results = await asyncio.gather(*(process_task(task, cache) for task in tasks))
#     return results

# # Example usage:
# if __name__ == "__main__":
#     # Create some sample tasks with dependencies.
#     # For example, Task C depends on Task A and Task B.
#     task_a = Task("AgentA")
#     task_b = Task("AgentB")
#     task_c = Task("AgentC", dependents=[task_a, task_b])
#     task_d = Task("AgentD", dependents=[task_c])
    
#     # The queue includes tasks that might have overlapping dependencies.
#     tasks = [task_c, task_d, task_a, task_b]
    
#     # Run the asynchronous processing.
#     results = asyncio.run(process_agent_queue(tasks))
#     print("All tasks processed. Results:")
#     for res in results:
#         print(res)