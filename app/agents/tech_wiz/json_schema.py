json_schema_tech_wiz = {
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
                    "description": "Raw response to prompt that includes technical insights, solutions, recommendations, and resources. Write a bullet point list, a paragraph, and a full report.",
                },
            },
            "required": ["raw_response"],
            "description": "The structured response including bullet points, a paragraph, and a report.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for input context and a structured response.",
}
