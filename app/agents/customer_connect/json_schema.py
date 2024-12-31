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
                "email": {
                    "type": "string",
                    "description": "The email response that should be used by the user.",
                },
                "follow_up": {
                    "type": "object",
                    "properties": {
                        "days_to_wait": {
                            "type": "integer",
                            "description": "Suggested amount of days to wait to follow-up.",
                        },
                        "suggestions": {
                            "type": "string",
                            "description": "Follow-up suggestions provided.",
                        },
                    },
                    "required": ["days_to_wait", "suggestions"],
                    "description": "Follow-up details, including timeframe and suggestions.",
                },
            },
            "required": ["email", "follow_up"],
            "description": "The response details, including the email and follow-up information.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for input context, email, and follow-up suggestions.",
}
