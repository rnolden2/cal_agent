json_schema_pro_mentor = {
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
                                        "description": "Array of up to 10 actionable steps to improve personally.",
                                    },
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
                                        "description": "Array of up to 10 actionable steps to improve professionally.",
                                    },
                                },
                            },
                            "required": ["explanation", "actions"],
                            "description": "Suggestions for professional improvement.",
                        },
                        "additional_content": {
                            "type": "string",
                            "description": "Any additional information that should be included.",
                        },
                        "past_feedback": {
                            "type": "string",
                            "description": "Explanation of how the input relates to previous feedback.",
                        },
                    },
                    "required": [
                        "personally",
                        "professionally",
                        "additional_content",
                        "past_feedback",
                    ],
                    "description": "How the user can improve personally and professionally with any additional helpful content and use of past feedback.",
                },
            },
            "required": ["raw_response"],
            "description": "The response object containing suggestions for improvement and feedback details.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for providing improvement suggestions based on input context and past feedback.",
}
