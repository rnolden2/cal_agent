json_schema_master = {
    "type": "object",
    "properties": {
        "context": {
            "type": "string",
            "description": "The context provided by the user.",
        },
        "timestamp": {
            "type": "integer",
            "description": "The timestamp in milliseconds when the input was generated.",
        },
        "response_id": {
            "type": "string",
            "description": "A unique identifier derived from the timestamp for integrity checks or uniqueness.",
        },
        "response": {
            "type": "object",
            "properties": {
                "task_description": {
                    "type": "string",
                    "description": "Summary of tasks derived from context.",
                },
                "agents_involved": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of agent names involved in the task.",
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
            "required": ["task_description", "agents_involved", "tasks"],
            "description": "Details of the response, including tasks and agents involved.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for the Master Agent managing tasks and routing them to individual agents.",
}
