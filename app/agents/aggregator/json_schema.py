json_schema_reviewer = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "Same agent name as in the agent list.",
        },
        "prompt": {
            "type": "string",
            "description": "The prompt.",
        },
        "response": {
            "type": "string",
            "description": "The prompt.",
        },
    },
    "required": ["agent", "prompt", "response"],
    "description": "Schema for Agent's response.",
}
