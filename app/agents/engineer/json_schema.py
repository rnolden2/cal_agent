json_schema_engineer = {
    "type": "object",
    "properties": {
        "context": {
            "type": "string",
            "description": "The context or engineering problem provided by the user.",
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
                    "description": "Raw response to prompt. that includes engineering concepts, resources, big picture analysis and recommendations.",
                },

            },
            "required": ["raw_response"],
            "description": "Details of the engineering concepts, resources, and recommendations.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for capturing the Engineer Agent's response, including concepts, resources, and analysis.",
}
