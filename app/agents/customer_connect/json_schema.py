json_schema_customer_connect = {
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
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for input context, timestamp, and response details.",
}
