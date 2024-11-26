json_schema = {
    "type": "object",
    "properties": {
        "content": {
            "type": "string",
            "description": "The content or context provided by the user.",
        },
        "timestamp": {
            "type": "integer",
            "description": "The timestamp in milliseconds when the input was generated.",
        },
        "timestamp_hash": {
            "type": "string",
            "description": "A hash derived from the timestamp for integrity checks or uniqueness.",
        },
        "task_description": {
            "type": "string",
            "description": "Summary of tasks derived from context.",
        },
        "agents_involved": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of agent names involved in the task. Agents are",
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent to handle the task.",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "Task-specific prompt crafted for the agent.",
                    },
                    "additional_context": {
                        "type": "string",
                        "description": "Provide additional context for the task.",
                    },
                },
                "required": ["agent_name", "prompt"],
                "description": "A single task assigned to an agent.",
            },
            "description": "Tasks routed to individual agents.",
        },
    },
    "required": [
        "content",
        "timestamp",
        "timestamp_hash",
        "task_description",
        "agents_involved",
        "tasks",
    ],
    "description": "Schema for the Master Agent managing tasks and routing them to individual agents.",
}
