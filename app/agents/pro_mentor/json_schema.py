json_schema_pro_mentor = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "Return PRO_MENTOR",
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
                    "description": "Markdown response to prompt that includes personal and professional improvement suggestions. Include explanations and actionable steps for improvement. Include any additional content and relate to past feedback.",
                },
            },
            "required": ["raw_response"],
            "description": "The response object containing suggestions for improvement and feedback details.",
        },
    },
    "required": ["agent","prompt", "response"],
    "description": "Schema for providing improvement suggestions based on input context and past feedback.",
}
