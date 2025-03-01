json_schema_customer_connect = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "The agent used to respond.",
        },
        "prompt": {
            "type": "string",
            "description": "The prompt provided by the user.",
        },
        "response": {
            "type": "object",
            "properties": {
                "raw_response": {
                    "type": "string",
                    "description": "Raw response to prompt.",
                },
                "additional_content": {
                    "type": "string",
                    "description": "Any additional information that should be included.",
                },
            },
            "required": ["raw_response", "additional_content"],
            "description": "The response details, including the email and follow-up information.",
        },
    },
    "required": ["agent", "prompt", "response"],
    "description": "Schema for customer connect response.",
}
