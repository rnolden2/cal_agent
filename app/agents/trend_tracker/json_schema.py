json_schema_trend_tracker = {
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
                    "description": "Raw response to prompt that includes deep research on trends, insights, and recommendations related. Provide kewords, related terms, and sources.",
                },
            },
            "required": ["raw_response"],
            "description": "A structured response.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for providing input context and search-related data.",
}
