json_schema = {
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
            "required": ["improvement", "past_feedback"],
            "description": "The response object containing suggestions for improvement and feedback details.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for providing improvement suggestions based on input context and past feedback.",
}
