json_schema_engineer = {
    "type": "object",
    "properties": {
        "agent": {
            "type": "string",
            "description": "The agent used to respond.",
        },
        "prompt": {
            "type": "string",
            "description": "The prompt or engineering problem provided by the user.",
        },
        "response": {
            "type": "object",
            "properties": {
                "raw_response": {
                    "type": "string",
                    "description": "Raw response to prompt. that includes engineering concepts, resources, big picture analysis and recommendations.",
                },
            },
            "required": ["raw_response"],
            "description": "Details of the engineering concepts, resources, and recommendations.",
        },
    },
    "required": ["agent","prompt", "response"],
    "description": "Schema for capturing the Engineer Agent's response, including concepts, resources, and analysis.",
}
