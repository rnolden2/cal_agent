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
                "bullet_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                    "description": "Array of bullet points, limited to a maximum of 5 items.",
                },
                "paragraph": {
                    "type": "string",
                    "description": "A detailed paragraph response.",
                },
                "report": {
                    "type": "string",
                    "description": "A full report provided as part of the response.",
                },
            },
            "required": ["bullet_points", "paragraph", "report"],
            "description": "The structured response including bullet points, a paragraph, and a report.",
        },
    },
    "required": ["content", "timestamp", "timestamp_hash", "response"],
    "description": "Schema for input context and a structured response.",
}