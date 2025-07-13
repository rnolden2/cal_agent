json_schema_master = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "The prompt provided by the user.",
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
                            "provider": {
                                "type": "string",
                                "description": "Task-specific prompt crafted for the agent.",
                            },
                            "model": {
                                "type": "integer",
                                "description": "Zero for a quick and easy task, one for a more complex task that can benefit from a reasoning model.",
                            },
                            "additional_context": {
                                "type": "string",
                                "description": "Provide additional context for the task.",
                            },
                        },
                        "required": [
                            "agent_name",
                            "prompt",
                            "provider",
                            "model",
                            "additional_context",
                        ],
                        "description": "A task assigned to an agent.",
                    },
                    "description": "Tasks routed to individual agents.",
                },
                "raw_response": {
                    "type": "string",
                    "description": "Raw response to prompt.",
                },
            },
            "required": [
                "task_description",
                "agents_involved",
                "tasks",
                "raw_response",
            ],
            "description": "Details of the response, including tasks and agents involved.",
        },
    },
    "required": ["prompt", "response"],
    "description": "Schema for the Master Agent managing tasks and routing them to individual agents.",
}
