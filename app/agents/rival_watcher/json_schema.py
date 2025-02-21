json_schema_rival_watcher = {
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
                    "description": "Raw response to prompt. that includes competitor-related data i.e. links descriptions etc.",
                },
            },
            "required": ["raw_response"],
            "description": "The response object containing competitor-related data.",
        },
    },
    "required": ["context", "timestamp", "response_id", "response"],
    "description": "Schema for providing input context and competitor-related data.",
}
