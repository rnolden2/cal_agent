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
                    "type": "string",
                    "description": "Markdown response to prompt that includes personal and professional improvement suggestions. Include explanations and actionable steps for improvement. Include any additional content and relate to past feedback.",
                },
            },
            "required": ["raw_response"],
            "description": "The response object containing suggestions for improvement and feedback details.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for providing improvement suggestions based on input context and past feedback.",
}
