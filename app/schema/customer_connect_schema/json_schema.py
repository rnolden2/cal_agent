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
        "response": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "Email response."}
            },
            "required": ["email"],
            "description": "The response details, including the email.",
        },
        "follow_up": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "integer",
                    "description": "The timestamp in milliseconds for the follow-up date.",
                },
                "suggestions": {
                    "type": "string",
                    "description": "Follow-up suggestions provided.",
                },
            },
            "required": ["date", "suggestions"],
            "description": "Follow-up details, including date and suggestions.",
        },
    },
    "required": ["content", "timestamp", "timestamp_hash", "response", "follow_up"],
    "description": "Schema for input context, response email, and follow-up suggestions.",
}
