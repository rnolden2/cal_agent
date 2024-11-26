json_schema = {
    "type": "object",
    "properties": {
        "input_context": {
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
            },
            "required": ["content", "timestamp", "timestamp_hash"],
            "description": "Contextual information provided as input.",
        },
        "improvement": {
            "type": "object",
            "properties": {
                "personally": {
                    "type": "object",
                    "properties": {
                        "explanation": {
                            "type": "string",
                            "description": "Explanation of how to improve personally.",
                        },
                        "actions": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "A specific step to improve personally.",
                            },
                            "maxItems": 10,
                            "description": "Array of up to 10 actionable steps for personal improvement.",
                        },
                    },
                    "required": ["explanation", "actions"],
                    "description": "Suggestions for personal improvement.",
                },
                "professionally": {
                    "type": "object",
                    "properties": {
                        "explanation": {
                            "type": "string",
                            "description": "Explanation of how to improve professionally.",
                        },
                        "actions": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "description": "A specific step to improve professionally.",
                            },
                            "maxItems": 10,
                            "description": "Array of up to 10 actionable steps for professional improvement.",
                        },
                    },
                    "required": ["explanation", "actions"],
                    "description": "Suggestions for professional improvement.",
                },
            },
            "required": ["personally", "professionally"],
            "description": "How the user can improve personally and professionally.",
        },
        "past_feedback": {
            "type": "string",
            "description": "Explanation of how the input relates to previous feedback.",
        },
    },
    "required": ["input_context", "improvement", "past_feedback"],
    "description": "Schema for providing improvement suggestions based on input context and past feedback.",
}
